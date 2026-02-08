"""
Registration schemas for A2W platform.

Differentiated registration for Aretan and Contratante roles with
password validation (8-16 chars, uppercase, number, special char).
"""
import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_password(password: str) -> str:
    """Validate password meets A2W requirements."""
    if len(password) < 8 or len(password) > 16:
        raise ValueError("Password must be 8-16 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("Password must contain at least one special character")
    return password


# =============================================================================
# Work Experience (nested in Aretan registration)
# =============================================================================

class WorkExperienceCreate(BaseModel):
    """Schema for creating a work experience entry."""

    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str | None = None
    display_order: int = 0


# =============================================================================
# Aretan Registration
# =============================================================================

class AretanRegistration(BaseModel):
    """Registration schema for Aretan (sport talent) users."""

    # User fields (required)
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=50)
    contact_email: EmailStr
    country: str = Field(min_length=1, max_length=100)

    # Profile fields (required)
    industry_id: UUID
    profession_id: UUID
    max_achievement_id: UUID
    sport_description: str = Field(min_length=1)
    languages: list[str] = Field(min_length=1)
    work_experiences: list[WorkExperienceCreate] = Field(min_length=1)

    # Profile fields (optional)
    professional_description: str | None = None
    employment_status: str | None = Field(
        None, pattern="^(employed|independent|open|unspecified)$"
    )
    social_networks: dict[str, str] | None = None

    # Terms
    accept_terms: bool

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        """Validate password strength."""
        return validate_password(v)

    @field_validator("accept_terms")
    @classmethod
    def must_accept_terms(cls, v: bool) -> bool:
        """Terms must be accepted."""
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v


# =============================================================================
# Contratante Registration
# =============================================================================

class ContractorRegistration(BaseModel):
    """Registration schema for Contratante (company/hirer) users."""

    # User fields (required)
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=50)
    contact_email: EmailStr
    country: str | None = None

    # Profile fields (required)
    entity_type: str = Field(pattern="^(individual|company)$")
    industry_id: UUID

    # Profile fields (optional)
    company_name: str | None = Field(None, max_length=200)
    company_size: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    description: str | None = None

    # Terms
    accept_terms: bool

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        """Validate password strength."""
        return validate_password(v)

    @field_validator("accept_terms")
    @classmethod
    def must_accept_terms(cls, v: bool) -> bool:
        """Terms must be accepted."""
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v


# =============================================================================
# Master List Schemas
# =============================================================================

class MasterListItemCreate(BaseModel):
    """Schema for creating a master list entry (admin)."""

    name: str = Field(min_length=1, max_length=200)
    display_order: int = 0


class MasterListItemUpdate(BaseModel):
    """Schema for updating a master list entry (admin)."""

    name: str | None = Field(None, min_length=1, max_length=200)
    is_active: bool | None = None
    display_order: int | None = None


class MasterListItemResponse(BaseModel):
    """Schema for master list item response."""

    model_config = {"from_attributes": True}

    id: UUID
    name: str
    is_active: bool
    display_order: int
