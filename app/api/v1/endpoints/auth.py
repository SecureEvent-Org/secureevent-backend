import tempfile
import os
import uuid
import time
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, GateVerificationResponse
from app.services.deepface_service import biometric_service

import io
import qrcode
from fastapi.responses import StreamingResponse
from app.core.security import create_access_token, decode_token

router = APIRouter()

# Umbral máximo de distancia coseno permitido para FaceNet (menor = más parecido)
COSINE_DISTANCE_THRESHOLD = 0.40

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    full_name: str = Form(...),
    curp: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    role: UserRole = Form(UserRole.ATTENDEE),
    tutor_id: Optional[uuid.UUID] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Registra un usuario en la BD extrayendo su embedding biométrico 
    a partir de una fotografía enviada.
    """
    # 1. Validar que la CURP no esté registrada previa si se proporciona
    if curp:
        existing_user = db.query(User).filter(User.curp == curp).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La CURP ingresada ya se encuentra registrada."
            )

    # 2. Guardar temporalmente la imagen para extraer el embedding con DeepFace
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen inválido. Debe ser JPG o PNG."
        )

    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Extraer el vector biométrico
        embedding = biometric_service.extract_embedding(temp_path)

        # 3. Crear la entidad User y guardar en la Base de Datos con pgvector
        new_user = User(
            full_name=full_name,
            curp=curp,
            email=email,
            role=role,
            tutor_id=tutor_id,
            face_embedding=embedding
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/verify-gate", response_model=GateVerificationResponse, status_code=status.HTTP_200_OK)
async def verify_gate_access(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Valida el acceso biométrico en puerta comparando la fotografía capturada
    contra los embeddings almacenados en PostgreSQL mediante distancia coseno (<=>).
    """
    start_time = time.perf_counter()

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen inválido. Debe ser JPG o PNG."
        )

    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # 1. Extraer embedding de la captura en puerta
        query_embedding = biometric_service.extract_embedding(temp_path)

        # 2. Búsqueda del vecino más cercano en PostgreSQL usando distancia coseno (<=>)
        distance_expr = User.face_embedding.cosine_distance(query_embedding)
        
        result = (
            db.query(User, distance_expr.label("distance"))
            .filter(User.face_embedding.isnot(None))
            .order_by(distance_expr)
            .first()
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 3. Evaluar si existe registro y si cumple el umbral de similitud
        if not result:
            return GateVerificationResponse(
                access="denied",
                message="No existen usuarios con biometría registrada en el sistema.",
                processing_time_ms=elapsed_ms
            )

        matched_user, distance = result
        distance = float(distance)
        similarity_pct = round(max(0.0, (1.0 - distance)) * 100, 2)

        if distance <= COSINE_DISTANCE_THRESHOLD:
            # Verificar si existe una alerta activa sobre esta persona
            if matched_user.is_missing:
                return GateVerificationResponse(
                    access="denied",
                    message="ALERTA DE SEGURIDAD: El usuario cuenta con un reporte activo de extravío.",
                    cosine_distance=round(distance, 4),
                    similarity_percentage=similarity_pct,
                    processing_time_ms=elapsed_ms,
                    user=matched_user
                )

            return GateVerificationResponse(
                access="granted",
                message="Acceso autorizado. Identidad biométrica verificada.",
                cosine_distance=round(distance, 4),
                similarity_percentage=similarity_pct,
                processing_time_ms=elapsed_ms,
                user=matched_user
            )
        else:
            return GateVerificationResponse(
                access="denied",
                message="Rostro no reconocido. La similitud no supera el umbral de seguridad.",
                cosine_distance=round(distance, 4),
                similarity_percentage=similarity_pct,
                processing_time_ms=elapsed_ms
            )

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante la verificación en puerta: {str(e)}"
        )
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/login-token", status_code=status.HTTP_200_OK)
def generate_user_token(user_id: uuid.UUID = Form(...), db: Session = Depends(get_db)):
    """
    Genera un token JWT de sesión para un usuario registrado (Asistente, Guardia o Admin).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": user.role.value
    }

@router.get("/qr/{user_id}", status_code=status.HTTP_200_OK)
def generate_backup_qr(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Genera una imagen PNG con el Código QR firmado (JWT) de respaldo
    para usuarios cuyo reconocimiento facial no sea claro en puerta.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # El contenido del QR es un token JWT firmado para evitar falsificaciones
    qr_payload = create_access_token(data={"sub": str(user.id), "type": "qr_backup"})

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

@router.post("/verify-qr", response_model=GateVerificationResponse, status_code=status.HTTP_200_OK)
def verify_qr_gate(qr_token: str = Form(...), db: Session = Depends(get_db)):
    """
    Valida el acceso en puerta leyendo el token contenido en el código QR de respaldo.
    """
    start_time = time.perf_counter()
    payload = decode_token(qr_token)
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == user_id).first()
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if not user:
        return GateVerificationResponse(
            access="denied",
            message="Usuario asociado al QR no encontrado.",
            processing_time_ms=elapsed_ms
        )

    if user.is_missing:
        return GateVerificationResponse(
            access="denied",
            message="ALERTA DE SEGURIDAD: El usuario cuenta con un reporte activo de extravío.",
            processing_time_ms=elapsed_ms,
            user=user
        )

    return GateVerificationResponse(
        access="granted",
        message="Acceso autorizado mediante Código QR de respaldo.",
        similarity_percentage=100.0,
        processing_time_ms=elapsed_ms,
        user=user
    )