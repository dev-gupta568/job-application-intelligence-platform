from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

ApplicationStatus = Literal[
    "Interested",
    "Applied",
    "Assessment",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
]
WorkMode = Literal["Remote", "Hybrid", "On-site"]
EmploymentType = Literal[
    "Full-time",
    "Part-time",
    "Contract",
    "Internship",
    "Temporary",
    "Volunteer",
    "Freelance",
]


class ApplicationFields(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    job_description: str | None = None
    company_website: HttpUrl | None = None
    job_posting_url: HttpUrl | None = None
    location: str | None = Field(default=None, max_length=200)
    work_mode: WorkMode | None = None
    employment_type: EmploymentType | None = None
    salary_min: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    salary_max: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    applied_on: date | None = None
    deadline: date | None = None
    status: ApplicationStatus = "Interested"
    recruiter_name: str | None = Field(default=None, max_length=160)
    recruiter_email: str | None = Field(default=None, max_length=320)
    recruiter_phone: str | None = Field(default=None, max_length=40)
    notes: str | None = None
    next_follow_up_at: datetime | None = None
    resume_version_id: UUID | None = None

    @field_validator("salary_currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @model_validator(mode="after")
    def check_salary_range(self) -> "ApplicationFields":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must not exceed salary_max")
        return self


class ApplicationCreate(ApplicationFields):
    pass


class ApplicationUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    job_title: str | None = Field(default=None, min_length=1, max_length=200)
    job_description: str | None = None
    company_website: HttpUrl | None = None
    job_posting_url: HttpUrl | None = None
    location: str | None = Field(default=None, max_length=200)
    work_mode: WorkMode | None = None
    employment_type: EmploymentType | None = None
    salary_min: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    salary_max: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    required_skills: list[str] | None = Field(default=None, max_length=100)
    applied_on: date | None = None
    deadline: date | None = None
    status: ApplicationStatus | None = None
    recruiter_name: str | None = Field(default=None, max_length=160)
    recruiter_email: str | None = Field(default=None, max_length=320)
    recruiter_phone: str | None = Field(default=None, max_length=40)
    notes: str | None = None
    next_follow_up_at: datetime | None = None
    resume_version_id: UUID | None = None

    @field_validator("company_name", "job_title", "required_skills")
    @classmethod
    def reject_null_for_non_nullable_fields(cls, value):
        if value is None:
            raise ValueError("This field cannot be null.")
        return value

    @field_validator("salary_currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @model_validator(mode="after")
    def check_salary_range(self) -> "ApplicationUpdate":
        updates = self.model_dump(exclude_unset=True)
        minimum = updates.get("salary_min")
        maximum = updates.get("salary_max")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("salary_min must not exceed salary_max")
        return self


class ApplicationRead(ApplicationFields):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationPage(BaseModel):
    items: list[ApplicationRead]
    total: int
    page: int
    page_size: int
