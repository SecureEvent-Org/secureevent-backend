from fastapi import APIRouter
from app.api.v1.endpoints import biometrics

api_router = APIRouter()

# Incluir el módulo de biometría bajo el prefijo /biometrics
api_router.include_router(biometrics.router, prefix="/biometrics", tags=["Biometría y Reconocimiento Facial"])