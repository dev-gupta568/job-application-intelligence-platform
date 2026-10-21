from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.models.application import APPLICATION_STATUSES, JobApplication
from app.models.related import ApplicationActivity, FollowUp, Interview
from app.schemas.analytics import (
    DashboardAnalytics,
    PeriodCount,
    RecentActivity,
    UpcomingFollowUp,
    UpcomingInterview,
    week_start,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
SUBMITTED_STATUSES = ("Applied", "Assessment", "Interview", "Offer", "Rejected", "Withdrawn")


def _percentage(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0.00")
    return (Decimal(numerator) * 100 / Decimal(denominator)).quantize(Decimal("0.01"))


def _weekly_counts(db: Session, user_id, today: date, weeks: int) -> list[PeriodCount]:
    current_week = week_start(today)
    starts = [
        current_week - timedelta(weeks=offset)
        for offset in reversed(range(weeks))
    ]
    boundaries = starts[1:] + [starts[-1] + timedelta(days=7)]
    expressions = [
        func.coalesce(
            func.sum(
                case(
                    (
                        (JobApplication.applied_on >= start)
                        & (JobApplication.applied_on < min(end, today + timedelta(days=1)))
                        & JobApplication.status.in_(SUBMITTED_STATUSES),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label(f"period_{index}")
        for index, (start, end) in enumerate(zip(starts, boundaries))
    ]
    counts = db.execute(
        select(*expressions).where(JobApplication.user_id == user_id)
    ).one()
    return [
        PeriodCount(period=start.isoformat(), applications=int(counts[index]))
        for index, start in enumerate(starts)
    ]


def _monthly_counts(db: Session, user_id, today: date, months: int) -> list[PeriodCount]:
    first_of_current_month = today.replace(day=1)
    starts = []
    year, month = first_of_current_month.year, first_of_current_month.month
    for offset in reversed(range(months)):
        current_index = year * 12 + month - 1 - offset
        starts.append(date(current_index // 12, current_index % 12 + 1, 1))

    boundaries = starts[1:]
    last = starts[-1]
    boundaries.append(date(last.year + (last.month == 12), last.month % 12 + 1, 1))
    expressions = [
        func.coalesce(
            func.sum(
                case(
                    (
                        (JobApplication.applied_on >= start)
                        & (JobApplication.applied_on < min(end, today + timedelta(days=1)))
                        & JobApplication.status.in_(SUBMITTED_STATUSES),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label(f"period_{index}")
        for index, (start, end) in enumerate(zip(starts, boundaries))
    ]
    counts = db.execute(
        select(*expressions).where(JobApplication.user_id == user_id)
    ).one()
    return [
        PeriodCount(period=start.strftime("%Y-%m"), applications=int(counts[index]))
        for index, start in enumerate(starts)
    ]


@router.get("/dashboard", response_model=DashboardAnalytics)
def dashboard(
    db: DbSession,
    user: CurrentUser,
    weeks: Annotated[int, Query(ge=1, le=26)] = 12,
    months: Annotated[int, Query(ge=1, le=24)] = 6,
) -> DashboardAnalytics:
    now = datetime.now(timezone.utc)
    today = date.today()

    status_counts = db.execute(
        select(JobApplication.status, func.count(JobApplication.id))
        .where(JobApplication.user_id == user.id)
        .group_by(JobApplication.status)
    ).all()
    distribution = {application_status: 0 for application_status in APPLICATION_STATUSES}
    distribution.update({application_status: count for application_status, count in status_counts})
    total_applications = sum(distribution.values())
    applied_jobs = distribution["Applied"]
    submitted_applications = sum(distribution[key] for key in SUBMITTED_STATUSES)
    offers_received = distribution["Offer"]
    rejected_applications = distribution["Rejected"]

    interview_applications = db.scalar(
        select(func.count(func.distinct(JobApplication.id)))
        .join(Interview, Interview.application_id == JobApplication.id)
        .where(
            JobApplication.user_id == user.id,
            JobApplication.status.in_(SUBMITTED_STATUSES),
            Interview.status != "Cancelled",
        )
    ) or 0
    interviews_scheduled = db.scalar(
        select(func.count(Interview.id))
        .join(JobApplication, JobApplication.id == Interview.application_id)
        .where(
            JobApplication.user_id == user.id,
            Interview.status == "Scheduled",
            Interview.scheduled_at >= now,
        )
    ) or 0

    interview_query = (
        select(Interview, JobApplication.company_name, JobApplication.job_title)
        .join(JobApplication, JobApplication.id == Interview.application_id)
        .where(
            JobApplication.user_id == user.id,
            Interview.status == "Scheduled",
            Interview.scheduled_at >= now,
        )
        .order_by(Interview.scheduled_at.asc())
        .limit(5)
    )
    upcoming_interviews = [
        UpcomingInterview(
            id=interview.id,
            company_name=company_name,
            job_title=job_title,
            round_name=interview.round_name,
            scheduled_at=interview.scheduled_at,
        )
        for interview, company_name, job_title in db.execute(interview_query)
    ]

    follow_up_query = (
        select(FollowUp, JobApplication.company_name, JobApplication.job_title)
        .join(JobApplication, JobApplication.id == FollowUp.application_id)
        .where(
            JobApplication.user_id == user.id,
            FollowUp.completed_at.is_(None),
            FollowUp.due_at <= now + timedelta(days=30),
        )
        .order_by(FollowUp.due_at.asc())
        .limit(5)
    )
    upcoming_follow_ups = []
    for follow_up, company_name, job_title in db.execute(follow_up_query):
        due_at = follow_up.due_at
        comparable_due_at = due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
        upcoming_follow_ups.append(
            UpcomingFollowUp(
                id=follow_up.id,
                company_name=company_name,
                job_title=job_title,
                title=follow_up.title,
                due_at=due_at,
                overdue=comparable_due_at < now,
            )
        )

    activity_query = (
        select(ApplicationActivity, JobApplication.company_name, JobApplication.job_title)
        .join(JobApplication, JobApplication.id == ApplicationActivity.application_id)
        .where(JobApplication.user_id == user.id)
        .order_by(ApplicationActivity.occurred_at.desc())
        .limit(10)
    )
    recent_activity = [
        RecentActivity(
            id=activity.id,
            company_name=company_name,
            job_title=job_title,
            event_type=activity.event_type,
            details=activity.details,
            previous_status=activity.previous_status,
            new_status=activity.new_status,
            occurred_at=activity.occurred_at,
        )
        for activity, company_name, job_title in db.execute(activity_query)
    ]

    return DashboardAnalytics(
        total_applications=total_applications,
        applied_jobs=applied_jobs,
        submitted_applications=submitted_applications,
        interviews_scheduled=interviews_scheduled,
        interview_conversion_rate=_percentage(interview_applications, submitted_applications),
        offers_received=offers_received,
        offer_conversion_rate=_percentage(offers_received, submitted_applications),
        rejected_applications=rejected_applications,
        application_success_rate=_percentage(offers_received, submitted_applications),
        status_distribution=distribution,
        weekly_applications=_weekly_counts(db, user.id, today, weeks),
        monthly_applications=_monthly_counts(db, user.id, today, months),
        upcoming_interviews=upcoming_interviews,
        upcoming_follow_ups=upcoming_follow_ups,
        recent_activity=recent_activity,
        generated_at=now,
    )
