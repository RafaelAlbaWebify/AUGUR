from __future__ import annotations

from pydantic import BaseModel, Field


class LanguageSkill(BaseModel):
    language: str = Field(min_length=1, max_length=80)
    cefr: str | None = Field(default=None, max_length=8)


class PersonalProfile(BaseModel):
    age: int | None = Field(default=None, ge=16, le=100)
    current_country: str | None = Field(default=None, max_length=3)
    citizenships: list[str] = Field(default_factory=list, max_length=8)
    profession: str | None = Field(default=None, max_length=160)
    skills: list[str] = Field(default_factory=list, max_length=100)
    languages: list[LanguageSkill] = Field(default_factory=list, max_length=30)
    household_size: int = Field(default=1, ge=1, le=20)
    monthly_net_income: float | None = Field(default=None, ge=0)
    liquid_savings: float | None = Field(default=None, ge=0)
    remote_work: bool = False
    preferences: dict[str, str | float | int | bool] = Field(default_factory=dict)


class PersonalProfileResponse(PersonalProfile):
    profile_id: str
    updated_at: str | None = None
