import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.application import JobApplication
    from app.models.user import User


class Interview(TimestampMixin, Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Scheduled', 'Completed', 'Cancelled')",
            name="ck_interviews_status",
        ),
        Index("ix_interviews_scheduled_at", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_name: Mapped[str] = mapped_column(String(120), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meeting_url: Mapped[str | None] = mapped_column(String(2048))
    preparation_notes: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Scheduled",
        server_default="Scheduled",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    application: Mapped["JobApplication"] = relationship(back_populates="interviews")


class FollowUp(TimestampMixin, Base):
    __tablename__ = "follow_ups"
    __table_args__ = (Index("ix_follow_ups_due_at", "due_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    application: Mapped["JobApplication"] = relationship(back_populates="follow_ups")


class ApplicationActivity(Base):
    __tablename__ = "application_activities"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('application_created', 'status_changed', "
            "'recruiter_communication', 'note_added', 'interview_scheduled', "
            "'follow_up_created')",
            name="ck_application_activities_event_type",
        ),
        CheckConstraint(
            "previous_status IS NULL OR previous_status IN "
            "('Interested', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')",
            name="ck_application_activities_previous_status",
        ),
        CheckConstraint(
            "new_status IS NULL OR new_status IN "
            "('Interested', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')",
            name="ck_application_activities_new_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    previous_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str | None] = mapped_column(String(20))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    application: Mapped["JobApplication"] = relationship(back_populates="activities")


class ResumeVersion(TimestampMixin, Base):
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    storage_key: Mapped[str | None] = mapped_column(String(512), unique=True)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="resume_versions")
    applications: Mapped[list["JobApplication"]] = relationship(back_populates="resume_version")


class SkillComparison(TimestampMixin, Base):
    __tablename__ = "skill_comparisons"
    __table_args__ = (
        CheckConstraint(
            "match_percentage >= 0 AND match_percentage <= 100",
            name="ck_skill_comparisons_match_percentage",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    user_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    matching_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    important_keywords: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    match_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="rule-based-v1",
        server_default="rule-based-v1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    application: Mapped["JobApplication"] = relationship(back_populates="skill_comparisons")
