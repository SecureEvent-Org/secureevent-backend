import numpy as np
from deepface import DeepFace
import logging

logger = logging.getLogger(__name__)

class BiometricService:
    @staticmethod
    def extract_embedding(image_path_or_array) -> list[float]:
        """
        Extrae un vector biométrico de 128 o 512 dimensiones
        utilizando el modelo FaceNet a través de DeepFace.
        """
        try:
            embeddings = DeepFace.represent(
                img_path=image_path_or_array,
                model_name="Facenet",
                enforce_detection=True
            )
            # Retorna la representación vectorial de la primera cara detectada
            return embeddings[0]["embedding"]
        except Exception as e:
            logger.error(f"Error extrayendo embedding facial: {str(e)}")
            raise ValueError("No se pudo detectar un rostro válido en la imagen.")

biometric_service = BiometricService()