from fastapi import APIRouter
from app.api.v1.endpoints import biometrics, auth

api_router = APIRouter()

# Incluir el módulo de biometría bajo el prefijo /biometrics
api_router.include_router(biometrics.router, prefix="/biometrics", tags=["Biometría y Reconocimiento Facial"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación y Usuarios"])