from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Crear motor de SQLAlchemy usando la URL de la base de datos
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Inicializa extensiones requeridas y la estructura de tablas."""
    with engine.connect() as connection:
        # Activa la extensión pgvector en PostgreSQL si no existe
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit()

def get_db():
    """Inyección de dependencia para obtener la sesión de BD en endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()