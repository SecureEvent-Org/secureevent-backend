from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.services.deepface_service import biometric_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Base de datos y extensión pgvector verificadas correctamente.")
    except Exception as e:
        print(f"Advertencia al conectar con la BD: {e}")
    
    # Precargar modelo FaceNet en memoria
    biometric_service.preload_model()
    print("Modelo biométrico FaceNet precargado en memoria.")

@app.get("/")
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "message": "Servidor Backend de SecureEvent operando correctamente."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}