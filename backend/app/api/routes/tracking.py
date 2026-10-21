from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.models.application import JobApplication
from app.models.related import ApplicationActivity, FollowUp, Interview
from app.schemas.tracking import (
    ActivityCreate,
    ActivityRead,
    FollowUpCreate,
    FollowUpRead,
    FollowUpUpdate,
    InterviewCreate,
    InterviewRead,
    InterviewUpdate,
)

router = APIRouter(tags=["interviews, follow-ups, and activity"])


def _owned_application(db: Session, user_id: UUID, application_id: UUID) -> JobApplication:
    application = db.scalar(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == user_id,
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application


def _owned_interview(db: Session, user_id: UUID, interview_id: UUID) -> Interview:
    interview = db.scalar(
        select(Interview)
        .join(JobApplication, Interview.application_id == JobApplication.id)
        .where(Interview.id == interview_id, JobApplication.user_id == user_id)
    )
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return interview


def _owned_follow_up(db: Session, user_id: UUID, follow_up_id: UUID) -> FollowUp:
    follow_up = db.scalar(
        select(FollowUp)
        .join(JobApplication, FollowUp.application_id == JobApplication.id)
        .where(FollowUp.id == follow_up_id, JobApplication.user_id == user_id)
    )
    if follow_up is None:
        raise HTTPException(status_code=404, detail="Follow-up not found.")
    return follow_up


@router.get("/interviews", response_model=list[InterviewRead])
def list_interviews(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[dict]:
    rows = db.execute(
        select(Interview, JobApplication.company_name, JobApplication.job_title)
        .join(JobApplication, Interview.application_id == JobApplication.id)
        .where(JobApplication.user_id == user.id)
        .order_by(Interview.scheduled_at.asc())
        .limit(limit)
    )
    return [
        {
            **{
                field: getattr(interview, field)
                for field in (
                    "id",
                    "application_id",
                    "round_name",
                    "scheduled_at",
                    "meeting_url",
                    "preparation_notes",
                    "feedback",
                    "status",
                )
            },
            "company_name": company_name,
            "job_title": job_title,
        }
        for interview, company_name, job_title in rows
    ]


@router.post(
    "/applications/{application_id}/interviews",
    response_model=InterviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_interview(
    application_id: UUID,
    payload: InterviewCreate,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    application = _owned_application(db, user.id, application_id)
    values = payload.model_dump()
    if values["meeting_url"] is not None:
        values["meeting_url"] = str(values["meeting_url"])
    interview = Interview(application_id=application.id, **values)
    db.add(interview)
    db.flush()
    db.add(
        ApplicationActivity(
            application_id=application.id,
            event_type="interview_scheduled",
            details=f"Interview scheduled: {interview.round_name}",
            occurred_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.refresh(interview)
    return {
        **{field: getattr(interview, field) for field in (
            "id", "application_id", "round_name", "scheduled_at", "meeting_url",
            "preparation_notes", "feedback", "status",
        )},
        "company_name": application.company_name,
        "job_title": application.job_title,
    }


@router.patch("/interviews/{interview_id}", response_model=InterviewRead)
def update_interview(
    interview_id: UUID,
    payload: InterviewUpdate,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    interview = _owned_interview(db, user.id, interview_id)
    application = interview.application
    changes = payload.model_dump(exclude_unset=True)
    if "meeting_url" in changes and changes["meeting_url"] is not None:
        changes["meeting_url"] = str(changes["meeting_url"])
    for field, value in changes.items():
        setattr(interview, field, value)
    db.commit()
    db.refresh(interview)
    return {
        **{field: getattr(interview, field) for field in (
            "id", "application_id", "round_name", "scheduled_at", "meeting_url",
            "preparation_notes", "feedback", "status",
        )},
        "company_name": application.company_name,
        "job_title": application.job_title,
    }


@router.get("/follow-ups", response_model=list[FollowUpRead])
def list_follow_ups(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[dict]:
    rows = db.execute(
        select(FollowUp, JobApplication.company_name, JobApplication.job_title)
        .join(JobApplication, FollowUp.application_id == JobApplication.id)
        .where(JobApplication.user_id == user.id)
        .order_by(FollowUp.completed_at.asc().nullsfirst(), FollowUp.due_at.asc())
        .limit(limit)
    )
    return [
        {
            **{
                field: getattr(follow_up, field)
                for field in ("id", "application_id", "title", "due_at", "notes", "completed_at")
            },
            "company_name": company_name,
            "job_title": job_title,
        }
        for follow_up, company_name, job_title in rows
    ]


@router.post(
    "/applications/{application_id}/follow-ups",
    response_model=FollowUpRead,
    status_code=status.HTTP_201_CREATED,
)
def create_follow_up(
    application_id: UUID,
    payload: FollowUpCreate,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    application = _owned_application(db, user.id, application_id)
    follow_up = FollowUp(application_id=application.id, **payload.model_dump())
    db.add(follow_up)
    db.flush()
    db.add(
        ApplicationActivity(
            application_id=application.id,
            event_type="follow_up_created",
            details=f"Follow-up reminder created: {follow_up.title}",
            occurred_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.refresh(follow_up)
    return {
        **{field: getattr(follow_up, field) for field in (
            "id", "application_id", "title", "due_at", "notes", "completed_at",
        )},
        "company_name": application.company_name,
        "job_title": application.job_title,
    }


@router.patch("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
def update_follow_up(
    follow_up_id: UUID,
    payload: FollowUpUpdate,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    follow_up = _owned_follow_up(db, user.id, follow_up_id)
    application = follow_up.application
    changes = payload.model_dump(exclude_unset=True)
    completed = changes.pop("completed", None)
    for field, value in changes.items():
        setattr(follow_up, field, value)
    if completed is not None:
        follow_up.completed_at = datetime.now(timezone.utc) if completed else None
    db.commit()
    db.refresh(follow_up)
    return {
        **{field: getattr(follow_up, field) for field in (
            "id", "application_id", "title", "due_at", "notes", "completed_at",
        )},
        "company_name": application.company_name,
        "job_title": application.job_title,
    }


@router.get(
    "/applications/{application_id}/activities",
    response_model=list[ActivityRead],
)
def list_activities(
    application_id: UUID,
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[ApplicationActivity]:
    _owned_application(db, user.id, application_id)
    return db.scalars(
        select(ApplicationActivity)
        .where(ApplicationActivity.application_id == application_id)
        .order_by(ApplicationActivity.occurred_at.desc())
        .limit(limit)
    ).all()


@router.post(
    "/applications/{application_id}/activities",
    response_model=ActivityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    application_id: UUID,
    payload: ActivityCreate,
    db: DbSession,
    user: CurrentUser,
) -> ApplicationActivity:
    application = _owned_application(db, user.id, application_id)
    activity = ApplicationActivity(
        application_id=application.id,
        event_type=payload.event_type,
        details=payload.details,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity
