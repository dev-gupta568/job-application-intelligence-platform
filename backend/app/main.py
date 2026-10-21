from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, applications, auth, skill_matching, tracking
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Job Application Tracker API",
    version="0.1.0",
    description="Private API for managing job applications and accounts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(tracking.router, prefix="/api/v1")
app.include_router(skill_matching.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
