from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir el router de la API v1 (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    # Inicializa la extensión vector en PostgreSQL al arrancar
    try:
        init_db()
        print("Base de datos y extensión pgvector verificadas correctamente.")
    except Exception as e:
        print(f"Advertencia al conectar con la BD: {e}")

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