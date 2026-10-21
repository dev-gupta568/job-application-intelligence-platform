from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.models.application import JobApplication
from app.models.related import SkillComparison
from app.schemas.skill_matching import SkillMatchRead, SkillMatchRequest
from app.services.skill_matching import analyze_skills

router = APIRouter(tags=["job intelligence"])


def _read_comparison(comparison: SkillComparison, application: JobApplication) -> SkillMatchRead:
    return SkillMatchRead(
        id=comparison.id,
        application_id=application.id,
        company_name=application.company_name,
        job_title=application.job_title,
        job_keywords=comparison.job_keywords,
        user_skills=comparison.user_skills,
        matching_skills=comparison.matching_skills,
        missing_skills=comparison.missing_skills,
        important_keywords=comparison.important_keywords,
        match_percentage=comparison.match_percentage,
        suggested_skills_to_learn=comparison.missing_skills[:5],
        resume_checklist=_resume_checklist(comparison.missing_skills),
        algorithm_version=comparison.algorithm_version,
        created_at=comparison.created_at,
    )


def _resume_checklist(missing_skills: list[str]) -> list[str]:
    checklist = [
        "Tailor your summary to the role using accurate, evidence-backed experience.",
        "Use important job terms naturally in relevant project or experience bullets.",
        "Support each listed skill with a concrete result, project, or example.",
    ]
    if missing_skills:
        checklist.append(
            "Address missing skills only when you have genuine experience; otherwise plan learning instead of claiming them."
        )
    else:
        checklist.append("No recognized missing skills; prioritize role-specific evidence and measurable outcomes.")
    return checklist


@router.post(
    "/applications/{application_id}/skill-match",
    response_model=SkillMatchRead,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_match(
    application_id: UUID,
    payload: SkillMatchRequest,
    db: DbSession,
    user: CurrentUser,
) -> SkillMatchRead:
    application = db.scalar(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == user.id,
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")

    description = payload.job_description or application.job_description or ""
    if not description and not application.required_skills:
        raise HTTPException(
            status_code=422,
            detail="Add a job description or required skills to analyze this application.",
        )
    analysis = analyze_skills(description, payload.user_skills, application.required_skills)
    if not analysis["job_keywords"]:
        raise HTTPException(
            status_code=422,
            detail=(
                "No supported skill keywords were found. Add the role's required skills "
                "or use terms from the supported rule-based vocabulary."
            ),
        )

    comparison = SkillComparison(
        application_id=application.id,
        job_keywords=analysis["job_keywords"],
        user_skills=analysis["user_skills"],
        matching_skills=analysis["matching_skills"],
        missing_skills=analysis["missing_skills"],
        important_keywords=analysis["important_keywords"],
        match_percentage=analysis["match_percentage"],
        algorithm_version=analysis["algorithm_version"],
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return _read_comparison(comparison, application)


@router.get("/skill-matches", response_model=list[SkillMatchRead])
def list_skill_matches(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[SkillMatchRead]:
    rows = db.execute(
        select(SkillComparison, JobApplication)
        .join(JobApplication, SkillComparison.application_id == JobApplication.id)
        .where(JobApplication.user_id == user.id)
        .order_by(SkillComparison.created_at.desc())
        .limit(limit)
    )
    return [_read_comparison(comparison, application) for comparison, application in rows]
