import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

# Esquema para responder los datos de un usuario registrado
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