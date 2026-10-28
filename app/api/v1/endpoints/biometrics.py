import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.deepface_service import biometric_service

router = APIRouter()

@router.post("/extract", status_code=status.HTTP_200_OK)
async def extract_face_embedding(file: UploadFile = File(...)):
    """
    Recibe una imagen (JPG/PNG), detecta el rostro y retorna 
    su vector biométrico (embedding) de 128 dimensiones usando FaceNet.
    """
    # 1. Validar el tipo de archivo recibido
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Debe ser JPG o PNG."
        )

    # 2. Guardar temporalmente la imagen subida en disco para que DeepFace la procese
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # 3. Extraer el embedding facial mediante el servicio de DeepFace
        embedding = biometric_service.extract_embedding(temp_path)

        return {
            "filename": file.filename,
            "dimensions": len(embedding),
            "embedding": embedding
        }

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar la imagen biométrica: {str(e)}"
        )
    finally:
        # 4. Eliminar el archivo temporal
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)