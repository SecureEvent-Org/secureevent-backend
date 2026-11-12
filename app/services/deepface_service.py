import numpy as np
from deepface import DeepFace
import logging

logger = logging.getLogger(__name__)

class BiometricService:
    def __init__(self):
        self.model_name = "Facenet"

    def preload_model(self):
        """
        Precarga los pesos del modelo FaceNet en memoria RAM al arrancar
        para garantizar respuestas en puerta inferiores a 2 segundos.
        """
        try:
            logger.info(f"Precargando modelo biométrico {self.model_name} en memoria...")
            DeepFace.build_model(self.model_name)
            logger.info(f"Modelo {self.model_name} cargado y listo en memoria.")
        except Exception as e:
            logger.error(f"Error precargando el modelo {self.model_name}: {str(e)}")

    def extract_embedding(self, image_path_or_array) -> list[float]:
        """
        Extrae un vector biométrico de 128 dimensiones usando el modelo precargado.
        """
        try:
            embeddings = DeepFace.represent(
                img_path=image_path_or_array,
                model_name=self.model_name,
                enforce_detection=True
            )
            return embeddings[0]["embedding"]
        except Exception as e:
            logger.error(f"Error extrayendo embedding facial: {str(e)}")
            raise ValueError("No se pudo detectar un rostro válido en la imagen.")

biometric_service = BiometricService()