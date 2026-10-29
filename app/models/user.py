import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    ATTENDEE = "attendee"   # Asistente adulto/tutor
    MINOR = "minor"         # Menor de edad
    GUARD = "guard"         # Personal de seguridad en puerta
    ADMIN = "admin"         # Administrador del evento

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(150), nullable=False)
    curp = Column(String(18), unique=True, nullable=True)  # Requerido para tutores/adultos
    email = Column(String(150), unique=True, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.ATTENDEE, nullable=False)
    
    # Campo Vectorial de 128 dimensiones para el embedding de DeepFace (FaceNet)
    face_embedding = Column(Vector(128), nullable=True)
    
    # Datos de vinculación de menores a tutores (Relación Tutor -> Menor)
    tutor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Estado de seguridad
    is_missing = Column(Boolean, default=False)  # True si existe reporte activo de extravío
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones relacionales de SQLAlchemy
    minors = relationship("User", backref="tutor", remote_side=[id])