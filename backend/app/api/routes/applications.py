from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.models.application import JobApplication
from app.models.related import ApplicationActivity, ResumeVersion
from app.schemas.application import (
    ApplicationCreate,
    ApplicationPage,
    ApplicationRead,
    ApplicationUpdate,
    ApplicationStatus,
    EmploymentType,
    WorkMode,
)

router = APIRouter(prefix="/applications", tags=["applications"])


def _owned_application(db: Session, user_id: UUID, application_id: UUID) -> JobApplication:
    application = db.scalar(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == user_id,
        )
    )
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    return application


def _verify_resume_owner(
    db: Session,
    user_id: UUID,
    resume_version_id: UUID | None,
) -> None:
    if resume_version_id is None:
        return
    resume = db.scalar(
        select(ResumeVersion.id).where(
            ResumeVersion.id == resume_version_id,
            ResumeVersion.user_id == user_id,
        )
    )
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found.",
        )


def _database_values(payload: ApplicationCreate | ApplicationUpdate, *, partial: bool) -> dict:
    values = payload.model_dump(exclude_unset=partial)
    for field in ("company_website", "job_posting_url"):
        if values.get(field) is not None:
            values[field] = str(values[field])
    return values


@router.post(
    "",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    payload: ApplicationCreate,
    db: DbSession,
    user: CurrentUser,
) -> JobApplication:
    values = _database_values(payload, partial=False)
    _verify_resume_owner(db, user.id, payload.resume_version_id)
    application = JobApplication(user_id=user.id, **values)
    db.add(application)
    db.flush()
    db.add(
        ApplicationActivity(
            application_id=application.id,
            event_type="application_created",
            new_status=application.status,
            occurred_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=ApplicationPage)
def list_applications(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    location: str | None = Query(default=None, max_length=200),
    work_mode: WorkMode | None = None,
    employment_type: EmploymentType | None = None,
    applied_from: date | None = None,
    applied_to: date | None = None,
    sort_by: Literal["applied_on", "deadline"] = "applied_on",
    sort_order: Literal["asc", "desc"] = "desc",
) -> ApplicationPage:
    filters = [JobApplication.user_id == user.id]
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            JobApplication.company_name.ilike(pattern)
            | JobApplication.job_title.ilike(pattern)
        )
    if status_filter:
        filters.append(JobApplication.status == status_filter)
    if location:
        filters.append(JobApplication.location.ilike(f"%{location.strip()}%"))
    if work_mode:
        filters.append(JobApplication.work_mode == work_mode)
    if employment_type:
        filters.append(JobApplication.employment_type == employment_type)
    if applied_from:
        filters.append(JobApplication.applied_on >= applied_from)
    if applied_to:
        filters.append(JobApplication.applied_on <= applied_to)
    if applied_from and applied_to and applied_from > applied_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="applied_from must not be after applied_to.",
        )

    sort_column = getattr(JobApplication, sort_by)
    ordering = sort_column.asc().nullslast() if sort_order == "asc" else sort_column.desc().nullslast()
    total = db.scalar(select(func.count()).select_from(JobApplication).where(*filters)) or 0
    items = db.scalars(
        select(JobApplication)
        .where(*filters)
        .order_by(ordering, JobApplication.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ApplicationPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{application_id}", response_model=ApplicationRead)
def read_application(
    application_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> JobApplication:
    return _owned_application(db, user.id, application_id)


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    db: DbSession,
    user: CurrentUser,
) -> JobApplication:
    application = _owned_application(db, user.id, application_id)
    changes = _database_values(payload, partial=True)
    _verify_resume_owner(db, user.id, changes.get("resume_version_id"))
    previous_status = application.status
    for field, value in changes.items():
        setattr(application, field, value)

    if application.salary_min is not None and application.salary_max is not None:
        if application.salary_min > application.salary_max:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="salary_min must not exceed salary_max.",
            )

    if application.status != previous_status:
        db.add(
            ApplicationActivity(
                application_id=application.id,
                event_type="status_changed",
                previous_status=previous_status,
                new_status=application.status,
                occurred_at=datetime.now(timezone.utc),
            )
        )
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> Response:
    application = _owned_application(db, user.id, application_id)
    db.delete(application)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
