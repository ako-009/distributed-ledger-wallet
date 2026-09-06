from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """What the client sends to register."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """What we send back after registration."""
    id: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    email: str | None = None


class LoginRequest(BaseModel):
    """What the client sends to login."""
    email: EmailStr
    password: str