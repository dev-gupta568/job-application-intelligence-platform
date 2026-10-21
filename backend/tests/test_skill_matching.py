from decimal import Decimal

from app.services.skill_matching import analyze_skills


def test_rule_based_analysis_normalizes_aliases_and_scores_extracted_terms():
    analysis = analyze_skills(
        "We need a Python engineer with FastAPI and PostgreSQL. "
        "Python and FastAPI experience are important.",
        [" python ", "JavaScript"],
        ["PostgreSQL"],
    )

    assert analysis["job_keywords"] == ["Python", "FastAPI", "PostgreSQL"]
    assert analysis["user_skills"] == ["Python", "JavaScript"]
    assert analysis["matching_skills"] == ["Python"]
    assert analysis["missing_skills"] == ["FastAPI", "PostgreSQL"]
    assert analysis["important_keywords"] == ["Python", "FastAPI", "PostgreSQL"]
    assert analysis["match_percentage"] == Decimal("33.33")
    assert analysis["suggested_skills_to_learn"] == ["FastAPI", "PostgreSQL"]
    assert analysis["algorithm_version"] == "rule-based-v1"


def test_custom_skills_match_only_as_whole_phrases_and_declared_requirements_are_included():
    analysis = analyze_skills(
        "The role needs advanced report design and SQL.",
        ["report design", "SQL"],
        ["Cloud architecture"],
    )

    assert analysis["job_keywords"] == ["report design", "SQL", "cloud architecture"]
    assert analysis["matching_skills"] == ["report design", "SQL"]
    assert analysis["missing_skills"] == ["cloud architecture"]


def test_skill_match_endpoint_persists_comparison_and_is_scoped_to_owner(client, account):
    created = client.post(
        "/api/v1/applications",
        headers=account["headers"],
        json={
            "company_name": "Northwind",
            "job_title": "Python Developer",
            "required_skills": ["FastAPI", "PostgreSQL"],
        },
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    response = client.post(
        f"/api/v1/applications/{application_id}/skill-match",
        headers=account["headers"],
        json={
            "job_description": "Python and FastAPI developer. PostgreSQL is required.",
            "user_skills": ["Python", "fastapi", "JavaScript"],
        },
    )

    assert response.status_code == 201
    comparison = response.json()
    assert comparison["company_name"] == "Northwind"
    assert comparison["job_keywords"] == ["Python", "FastAPI", "PostgreSQL"]
    assert comparison["matching_skills"] == ["Python", "FastAPI"]
    assert comparison["missing_skills"] == ["PostgreSQL"]
    assert comparison["important_keywords"] == ["FastAPI", "PostgreSQL"]
    assert comparison["match_percentage"] == "66.67"
    assert comparison["suggested_skills_to_learn"] == ["PostgreSQL"]
    assert comparison["algorithm_version"] == "rule-based-v1"

    history = client.get("/api/v1/skill-matches", headers=account["headers"])
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["id"] == comparison["id"]

    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": "skill-owner@example.com",
            "display_name": "Other user",
            "password": "another-long-test-password",
        },
    )
    assert other.status_code == 201
    other_login = client.post(
        "/api/v1/auth/login",
        data={
            "username": "skill-owner@example.com",
            "password": "another-long-test-password",
        },
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    denied = client.post(
        f"/api/v1/applications/{application_id}/skill-match",
        headers=other_headers,
        json={
            "job_description": "Python developer",
            "user_skills": ["Python"],
        },
    )
    assert denied.status_code == 404
    assert client.get("/api/v1/skill-matches", headers=other_headers).json() == []


def test_skill_match_uses_saved_application_data_and_rejects_unrecognized_input(client, account):
    created = client.post(
        "/api/v1/applications",
        headers=account["headers"],
        json={
            "company_name": "Saved Job",
            "job_title": "Frontend Engineer",
            "job_description": "React and TypeScript experience required.",
            "required_skills": ["React"],
        },
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    response = client.post(
        f"/api/v1/applications/{application_id}/skill-match",
        headers=account["headers"],
        json={"user_skills": ["React", "TypeScript"]},
    )
    assert response.status_code == 201
    assert response.json()["match_percentage"] == "100.00"

    no_source = client.post(
        "/api/v1/applications",
        headers=account["headers"],
        json={"company_name": "No Description", "job_title": "Generalist"},
    )
    assert no_source.status_code == 201
    invalid = client.post(
        f"/api/v1/applications/{no_source.json()['id']}/skill-match",
        headers=account["headers"],
        json={"user_skills": ["Python"]},
    )
    assert invalid.status_code == 422

    no_recognized_terms = client.post(
        f"/api/v1/applications/{no_source.json()['id']}/skill-match",
        headers=account["headers"],
        json={
            "job_description": "Looking for a candidate who enjoys solving puzzles.",
            "user_skills": ["Python"],
        },
    )
    assert no_recognized_terms.status_code == 422


def test_skill_matching_is_case_insensitive_for_user_and_posting_aliases():
    analysis = analyze_skills(
        "Looking for a REACT.JS developer with POSTGRES experience.",
        ["react", "postgresql"],
        [],
    )
    assert analysis["job_keywords"] == ["React", "PostgreSQL"]
    assert analysis["matching_skills"] == ["React", "PostgreSQL"]
    assert analysis["match_percentage"] == Decimal("100.00")


def test_skill_matching_avoids_short_alias_false_positive():
    analysis = analyze_skills(
        "Please go through this React.js specification.",
        ["JavaScript", "Go", "React"],
        [],
    )

    assert analysis["job_keywords"] == ["React"]
    assert analysis["matching_skills"] == ["React"]
