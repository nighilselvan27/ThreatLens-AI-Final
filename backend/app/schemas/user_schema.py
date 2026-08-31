from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    ADMIN = "Admin"
    SECURITY_ANALYST = "Security Analyst"


# Register Request Schema
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.SECURITY_ANALYST


# Login Request Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Profile Update Request Schema
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


# User Response Schema
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# JWT Token Response Schema
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# JWT Token Payload Data Schema
class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None