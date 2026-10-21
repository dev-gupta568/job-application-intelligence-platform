from uuid import UUID


def test_application_crud_and_search(client, account):
    headers = account["headers"]
    created = client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_name": "Northwind",
            "job_title": "Python Developer",
            "status": "Applied",
            "required_skills": ["Python", "PostgreSQL"],
            "applied_on": "2026-10-20",
            "company_website": "https://northwind.example",
        },
    )
    assert created.status_code == 201
    application = created.json()
    assert application["user_id"] == account["id"]
    assert application["applied_on"] == "2026-10-20"
    assert application["company_website"] == "https://northwind.example/"

    results = client.get(
        "/api/v1/applications?search=python&status=Applied&page=1&page_size=10",
        headers=headers,
    )
    assert results.status_code == 200
    assert results.json()["total"] == 1
    assert results.json()["items"][0]["company_name"] == "Northwind"

    updated = client.patch(
        f"/api/v1/applications/{application['id']}",
        headers=headers,
        json={"status": "Interview", "applied_on": "2026-10-21"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "Interview"
    assert updated.json()["applied_on"] == "2026-10-21"

    deleted = client.delete(
        f"/api/v1/applications/{application['id']}",
        headers=headers,
    )
    assert deleted.status_code == 204


def test_application_routes_require_authentication(client):
    response = client.get("/api/v1/applications")
    assert response.status_code == 401


def test_cors_allows_the_local_vite_origin(client):
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_user_cannot_read_another_users_application(client, account):
    other_registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "another@example.com",
            "display_name": "Another user",
            "password": "a-different-test-password",
        },
    )
    assert other_registration.status_code == 201
    other_login = client.post(
        "/api/v1/auth/login",
        data={"username": "another@example.com", "password": "a-different-test-password"},
    )
    other_headers = {
        "Authorization": f"Bearer {other_login.json()['access_token']}",
    }

    created = client.post(
        "/api/v1/applications",
        headers=account["headers"],
        json={"company_name": "Private Co", "job_title": "Engineer"},
    )
    assert created.status_code == 201

    application_id = created.json()["id"]
    response = client.get(
        f"/api/v1/applications/{application_id}",
        headers=other_headers,
    )
    assert response.status_code == 404

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        headers=other_headers,
        json={"status": "Offer"},
    )
    assert response.status_code == 404

    response = client.delete(
        f"/api/v1/applications/{application_id}",
        headers=other_headers,
    )
    assert response.status_code == 404

    response = client.get("/api/v1/applications", headers=other_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_invalid_application_data_is_rejected(client, account):
    response = client.post(
        "/api/v1/applications",
        headers=account["headers"],
        json={
            "company_name": "Northwind",
            "job_title": "Engineer",
            "status": "Hired",
            "salary_min": 150000,
            "salary_max": 100000,
        },
    )
    assert response.status_code == 422


def test_cannot_attach_another_users_resume(client, account):
    from app.models.related import ResumeVersion

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "resume-owner@example.com",
            "display_name": "Resume Owner",
            "password": "another-long-test-password",
        },
    )
    assert registration.status_code == 201

    with client.session_factory() as session:
        resume = ResumeVersion(
            user_id=UUID(registration.json()["id"]),
            name="Private resume",
        )
        session.add(resume)
        session.commit()
        resume_id = str(resume.id)

    response = client.post(
        "/api/v1/applications",
        headers=account["headers"],
        json={
            "company_name": "Example Co",
            "job_title": "Engineer",
            "resume_version_id": resume_id,
        },
    )
    assert response.status_code == 404
