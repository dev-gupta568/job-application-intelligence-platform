from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SkillMatchRequest(BaseModel):
    job_description: str | None = Field(default=None, max_length=30000)
    user_skills: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("job_description")
    @classmethod
    def normalize_job_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("user_skills")
    @classmethod
    def normalize_user_skills(cls, values: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(skill.strip() for skill in values if skill.strip()))
        if not cleaned:
            raise ValueError("Enter at least one skill.")
        return cleaned


class SkillMatchRead(BaseModel):
    id: UUID
    application_id: UUID
    company_name: str
    job_title: str
    job_keywords: list[str]
    user_skills: list[str]
    matching_skills: list[str]
    missing_skills: list[str]
    important_keywords: list[str]
    match_percentage: Decimal
    suggested_skills_to_learn: list[str]
    resume_checklist: list[str]
    algorithm_version: str
    created_at: datetime
