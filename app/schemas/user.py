"""
User schemas for API validation.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str, info) -> str:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        - Not a common weak password
        - Not too similar to username
        
        Args:
            v: Password to validate
            info: Validation info containing other field values
            
        Returns:
            Validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        # Check for uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&* etc.)"
            )
        
        # List of common weak passwords (check base words, not full patterns)
        # We check if these weak words appear in the password
        weak_password_bases = {
            "password",
            "12345678",
            "123456789",
            "1234567890",
            "qwerty",
            "letmein",
            "welcome",
            "admin",
            "iloveyou",
            "monkey",
            "dragon",
            "master",
            "sunshine",
            "princess",
            "shadow",
            "superman",
            "michael",
        }
        
        # Check if password contains any weak base words
        password_lower = v.lower()
        for weak_base in weak_password_bases:
            if weak_base in password_lower:
                raise ValueError("Password is too common. Please choose a stronger password")
        
        # Check similarity to username (if available)
        if info.data and "username" in info.data:
            username = info.data["username"]
            if username and username.lower() in v.lower():
                raise ValueError("Password must not contain your username")
        
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)  # Frontend compatibility: alias for full_name
    avatar_url: Optional[str] = Field(None, max_length=500)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response (without password)."""

    id: UUID
    is_active: bool
    is_verified: bool
    oauth_provider: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    
    @computed_field
    @property
    def display_name(self) -> Optional[str]:
        """Alias for full_name to maintain frontend compatibility."""
        return self.full_name


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class TokenData(BaseModel):
    """Schema for JWT token payload."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    """Schema for email verification request."""
    
    token: str = Field(..., min_length=1, description="Verification token from email")


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""
    
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Schema for changing user password."""
    
    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str, info) -> str:
        """
        Validate new password meets security requirements.
        
        Reuses validation logic from UserCreate to ensure consistency.
        """
        # Check for uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&* etc.)"
            )
        
        # List of common weak passwords
        weak_password_bases = {
            "password",
            "12345678",
            "123456789",
            "1234567890",
            "qwerty",
            "letmein",
            "welcome",
            "admin",
            "iloveyou",
            "monkey",
            "dragon",
            "master",
            "sunshine",
            "princess",
            "shadow",
            "superman",
            "michael",
        }
        
        # Check if password contains any weak base words
        password_lower = v.lower()
        for weak_base in weak_password_bases:
            if weak_base in password_lower:
                raise ValueError("Password is too common. Please choose a stronger password")
        
        return v


class ChangePasswordResponse(BaseModel):
    """Schema for password change response."""
    
    message: str
    updated_at: datetime


class UserStatsResponse(BaseModel):
    """Schema for user statistics response."""
    
    total_votes: int = Field(..., description="Total votes cast by user")
    total_comments: int = Field(..., description="Total comments posted by user")
    bookmarks_count: int = Field(..., description="Total articles bookmarked")
    reading_history_count: int = Field(..., description="Total articles read")
