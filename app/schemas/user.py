import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from app.models.user import UserRole

class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    curp: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole
    is_missing: bool
    tutor_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

# Nuevo esquema para la respuesta del punto de acceso
class GateVerificationResponse(BaseModel):
    access: Literal["granted", "denied"]
    message: str
    cosine_distance: Optional[float] = None
    similarity_percentage: Optional[float] = None
    processing_time_ms: float
    user: Optional[UserResponse] = None