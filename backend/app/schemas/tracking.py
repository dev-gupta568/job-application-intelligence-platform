from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

InterviewStatus = Literal["Scheduled", "Completed", "Cancelled"]
ActivityType = Literal["recruiter_communication", "note_added"]


def require_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("A timezone is required.")
    return value.astimezone(timezone.utc)


class InterviewCreate(BaseModel):
    round_name: str = Field(min_length=1, max_length=120)
    scheduled_at: datetime
    meeting_url: HttpUrl | None = None
    preparation_notes: str | None = None
    feedback: str | None = None

    @field_validator("round_name")
    @classmethod
    def normalize_round_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("The interview round cannot be blank.")
        return cleaned

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, value: datetime) -> datetime:
        return require_timezone(value)


class InterviewUpdate(BaseModel):
    round_name: str | None = Field(default=None, min_length=1, max_length=120)
    scheduled_at: datetime | None = None
    meeting_url: HttpUrl | None = None
    preparation_notes: str | None = None
    feedback: str | None = None
    status: InterviewStatus | None = None

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, value: datetime | None) -> datetime:
        if value is None:
            raise ValueError("The scheduled date cannot be null.")
        return require_timezone(value)

    @field_validator("round_name")
    @classmethod
    def normalize_round_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("The interview round cannot be blank.")
        return cleaned

    @field_validator("status")
    @classmethod
    def reject_null_required_values(cls, value):
        if value is None:
            raise ValueError("This field cannot be null.")
        return value


class InterviewRead(BaseModel):
    id: UUID
    application_id: UUID
    company_name: str
    job_title: str
    round_name: str
    scheduled_at: datetime
    meeting_url: str | None
    preparation_notes: str | None
    feedback: str | None
    status: InterviewStatus

    model_config = ConfigDict(from_attributes=True)


class FollowUpCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_at: datetime
    notes: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("The reminder title cannot be blank.")
        return cleaned

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime) -> datetime:
        return require_timezone(value)


class FollowUpUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_at: datetime | None = None
    notes: str | None = None
    completed: bool | None = None

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime:
        if value is None:
            raise ValueError("The due date cannot be null.")
        return require_timezone(value)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("The reminder title cannot be blank.")
        return cleaned


class FollowUpRead(BaseModel):
    id: UUID
    application_id: UUID
    company_name: str
    job_title: str
    title: str
    due_at: datetime
    notes: str | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ActivityCreate(BaseModel):
    event_type: ActivityType
    details: str = Field(min_length=1, max_length=5000)

    @field_validator("details")
    @classmethod
    def normalize_details(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Activity details cannot be blank.")
        return cleaned


class ActivityRead(BaseModel):
    id: UUID
    event_type: str
    details: str | None
    previous_status: str | None
    new_status: str | None
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)
