import tempfile
import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.services.deepface_service import biometric_service

router = APIRouter()

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