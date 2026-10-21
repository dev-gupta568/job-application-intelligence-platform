from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.application import ApplicationStatus


class PeriodCount(BaseModel):
    period: str
    applications: int


class UpcomingInterview(BaseModel):
    id: UUID
    company_name: str
    job_title: str
    round_name: str
    scheduled_at: datetime


class UpcomingFollowUp(BaseModel):
    id: UUID
    company_name: str
    job_title: str
    title: str
    due_at: datetime
    overdue: bool


class RecentActivity(BaseModel):
    id: UUID
    company_name: str
    job_title: str
    event_type: Literal[
        "application_created",
        "status_changed",
        "recruiter_communication",
        "note_added",
        "interview_scheduled",
        "follow_up_created",
    ]
    details: str | None
    previous_status: ApplicationStatus | None
    new_status: ApplicationStatus | None
    occurred_at: datetime


class DashboardAnalytics(BaseModel):
    total_applications: int
    applied_jobs: int
    submitted_applications: int
    interviews_scheduled: int
    interview_conversion_rate: Decimal
    offers_received: int
    offer_conversion_rate: Decimal
    rejected_applications: int
    application_success_rate: Decimal
    status_distribution: dict[ApplicationStatus, int]
    weekly_applications: list[PeriodCount]
    monthly_applications: list[PeriodCount]
    upcoming_interviews: list[UpcomingInterview]
    upcoming_follow_ups: list[UpcomingFollowUp]
    recent_activity: list[RecentActivity]
    generated_at: datetime


def week_start(value: date) -> date:
    return value.fromordinal(value.toordinal() - value.weekday())
