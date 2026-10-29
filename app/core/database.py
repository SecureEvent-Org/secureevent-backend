from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Inicializa la extensión vector y genera las tablas de la BD."""
    # Importar los modelos aquí para que SQLAlchemy reconozca las tablas
    from app.models.user import User  # noqa: F401

    with engine.connect() as connection:
        # 1. Activar la extensión pgvector en PostgreSQL
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit()

    # 2. Crear las tablas si no existen
    Base.metadata.create_all(bind=engine)

def get_db():
    """Inyección de dependencia para obtener la sesión de BD en los endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()