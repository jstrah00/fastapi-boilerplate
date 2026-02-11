"""
Profile schemas for A2W platform.

Response and update schemas for Aretan and Contratante profiles,
including work experience and nested master list references.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =============================================================================
# Master List Reference (nested in profile responses)
# =============================================================================

class MasterListRef(BaseModel):
    """Minimal reference to a master list item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


# =============================================================================
# Work Experience
# =============================================================================

class WorkExperienceResponse(BaseModel):
    """Response schema for a work experience entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    start_date: date
    end_date: date | None = None
    description: str | None = None
    display_order: int


class WorkExperienceCreate(BaseModel):
    """Schema for creating a work experience entry."""

    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str | None = None
    display_order: int = 0


class WorkExperienceUpdate(BaseModel):
    """Schema for updating a work experience entry."""

    title: str | None = Field(None, min_length=1, max_length=200)
    company: str | None = Field(None, min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    display_order: int | None = None


# =============================================================================
# Aretan Profile
# =============================================================================

class AretanProfileResponse(BaseModel):
    """Response schema for Aretan profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    # Master list references (multi-select)
    industries: list[MasterListRef] = []
    professions: list[MasterListRef] = []
    max_achievement: MasterListRef | None = None

    # Raw IDs for edit forms
    industry_ids: list[UUID] | None = None
    profession_ids: list[UUID] | None = None

    # Text fields
    sport_description: str | None = None
    professional_description: str | None = None
    employment_status: str | None = None
    languages: list[str] | None = None
    social_networks: dict[str, str] | None = None

    # Visibility
    phone_visible: bool = False
    email_visible: bool = False

    # Work experience
    work_experiences: list[WorkExperienceResponse] = []

    created_at: datetime
    updated_at: datetime


class AretanProfileUpdate(BaseModel):
    """Schema for updating an Aretan profile."""

    industry_ids: list[UUID] | None = None
    profession_ids: list[UUID] | None = None
    max_achievement_id: UUID | None = None
    sport_description: str | None = None
    professional_description: str | None = None
    employment_status: str | None = Field(
        None, pattern="^(employed|independent|open|unspecified)$"
    )
    languages: list[str] | None = None
    social_networks: dict[str, str] | None = None
    phone_visible: bool | None = None
    email_visible: bool | None = None


# =============================================================================
# Contractor Profile
# =============================================================================

class ContractorProfileResponse(BaseModel):
    """Response schema for Contractor profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    entity_type: str
    company_name: str | None = None
    company_size: str | None = None
    website: str | None = None
    industry: MasterListRef | None = None
    description: str | None = None

    created_at: datetime
    updated_at: datetime


class ContractorProfileUpdate(BaseModel):
    """Schema for updating a Contractor profile."""

    entity_type: str | None = Field(None, pattern="^(individual|company)$")
    company_name: str | None = Field(None, max_length=200)
    company_size: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    industry_id: UUID | None = None
    description: str | None = None


# =============================================================================
# User Info Update (basic fields)
# =============================================================================

class UserInfoUpdate(BaseModel):
    """Schema for updating basic user info."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=100)
    email_notifications_enabled: bool | None = None


# =============================================================================
# Public Profile (combined user + profile data)
# =============================================================================

class PublicUserInfo(BaseModel):
    """Public user info shown in profiles."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None
    country: str | None = None
    role: str
    status: str

    # Contact info (conditional on visibility)
    phone: str | None = None
    email: str | None = None


class AretanPublicProfile(BaseModel):
    """Full public profile for an Aretan user."""

    user: PublicUserInfo
    profile: AretanProfileResponse


class ContractorPublicProfile(BaseModel):
    """Full public profile for a Contractor user."""

    user: PublicUserInfo
    profile: ContractorProfileResponse


class UnifiedPublicProfile(BaseModel):
    """Unified public profile that works for any role."""

    user: PublicUserInfo
    aretan_profile: AretanProfileResponse | None = None
    contractor_profile: ContractorProfileResponse | None = None
