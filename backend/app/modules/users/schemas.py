from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    email_verified: bool
    role: str
    created_at: datetime
    updated_at: datetime
    locked_until: Optional[datetime] = None

    class Config:
        from_attributes = True


# Admin-specific schemas

class UserListFilters(BaseModel):
    """Filters for listing users."""
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|user|guest)$")
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserCreateByAdmin(BaseModel):
    """Schema for admin creating a new user."""
    email: EmailStr
    username: str
    role: str = Field("user", pattern="^(admin|user|guest)$")
    password: Optional[str] = None  # If None, generate random password


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|user|guest)$")
    is_active: Optional[bool] = None


class LockUserRequest(BaseModel):
    """Schema for locking a user account."""
    duration_hours: int = Field(24, gt=0, le=8760)  # Max 1 year


class AdminResetPasswordResponse(BaseModel):
    """Response when admin resets user password."""
    message: str
    temporary_password: str
