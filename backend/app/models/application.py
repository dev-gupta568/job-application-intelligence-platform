import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
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
    from app.models.related import (
        ApplicationActivity,
        FollowUp,
        Interview,
        ResumeVersion,
        SkillComparison,
    )
    from app.models.user import User


APPLICATION_STATUSES = (
    "Interested",
    "Applied",
    "Assessment",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
)


class JobApplication(TimestampMixin, Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Interested', 'Applied', 'Assessment', 'Interview', "
            "'Offer', 'Rejected', 'Withdrawn')",
            name="ck_job_applications_status",
        ),
        CheckConstraint(
            "work_mode IS NULL OR work_mode IN ('Remote', 'Hybrid', 'On-site')",
            name="ck_job_applications_work_mode",
        ),
        CheckConstraint(
            "employment_type IS NULL OR employment_type IN "
            "('Full-time', 'Part-time', 'Contract', 'Internship', 'Temporary', "
            "'Volunteer', 'Freelance')",
            name="ck_job_applications_employment_type",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_job_applications_salary_range",
        ),
        Index("ix_job_applications_user_status", "user_id", "status"),
        Index("ix_job_applications_user_applied_on", "user_id", "applied_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    job_description: Mapped[str | None] = mapped_column(Text)
    company_website: Mapped[str | None] = mapped_column(String(2048))
    job_posting_url: Mapped[str | None] = mapped_column(String(2048))
    location: Mapped[str | None] = mapped_column(String(200))
    work_mode: Mapped[str | None] = mapped_column(String(20))
    employment_type: Mapped[str | None] = mapped_column(String(20))
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salary_currency: Mapped[str | None] = mapped_column(String(3))
    required_skills: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    applied_on: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Interested",
        server_default="Interested",
    )
    recruiter_name: Mapped[str | None] = mapped_column(String(160))
    recruiter_email: Mapped[str | None] = mapped_column(String(320))
    recruiter_phone: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="SET NULL"),
        index=True,
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

    user: Mapped["User"] = relationship(back_populates="applications")
    resume_version: Mapped["ResumeVersion | None"] = relationship(back_populates="applications")
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    activities: Mapped[list["ApplicationActivity"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    skill_comparisons: Mapped[list["SkillComparison"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
