from datetime import datetime, timedelta, timezone


def create_application(client, headers, company="Example Co"):
    response = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_name": company, "job_title": "Software Engineer"},
    )
    assert response.status_code == 201
    return response.json()


def test_interview_and_follow_up_lifecycle(client, account):
    application = create_application(client, account["headers"])
    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    interview = client.post(
        f"/api/v1/applications/{application['id']}/interviews",
        headers=account["headers"],
        json={
            "round_name": "Technical",
            "scheduled_at": scheduled_at,
            "meeting_url": "https://meet.example.com/room",
            "preparation_notes": "Review project architecture.",
        },
    )
    assert interview.status_code == 201
    interview_data = interview.json()
    assert interview_data["company_name"] == "Example Co"
    assert interview_data["status"] == "Scheduled"

    completed_interview = client.patch(
        f"/api/v1/interviews/{interview_data['id']}",
        headers=account["headers"],
        json={"status": "Completed", "feedback": "Good technical discussion."},
    )
    assert completed_interview.status_code == 200
    assert completed_interview.json()["feedback"] == "Good technical discussion."
    assert completed_interview.json()["status"] == "Completed"
    assert client.get("/api/v1/interviews", headers=account["headers"]).json()[0]["id"] == interview_data["id"]

    follow_up = client.post(
        f"/api/v1/applications/{application['id']}/follow-ups",
        headers=account["headers"],
        json={
            "title": "Send thank-you note",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "notes": "Mention the product roadmap.",
        },
    )
    assert follow_up.status_code == 201
    follow_up_data = follow_up.json()
    assert follow_up_data["completed_at"] is None

    completed_follow_up = client.patch(
        f"/api/v1/follow-ups/{follow_up_data['id']}",
        headers=account["headers"],
        json={"completed": True},
    )
    assert completed_follow_up.status_code == 200
    assert completed_follow_up.json()["completed_at"] is not None
    assert client.get("/api/v1/follow-ups", headers=account["headers"]).json()[0]["id"] == follow_up_data["id"]

    timeline = client.get(
        f"/api/v1/applications/{application['id']}/activities",
        headers=account["headers"],
    )
    assert timeline.status_code == 200
    assert {item["event_type"] for item in timeline.json()} >= {
        "application_created",
        "interview_scheduled",
        "follow_up_created",
    }


def test_timeline_records_recruiter_communication_and_notes(client, account):
    application = create_application(client, account["headers"])

    communication = client.post(
        f"/api/v1/applications/{application['id']}/activities",
        headers=account["headers"],
        json={
            "event_type": "recruiter_communication",
            "details": "Recruiter confirmed the next-round schedule.",
        },
    )
    note = client.post(
        f"/api/v1/applications/{application['id']}/activities",
        headers=account["headers"],
        json={"event_type": "note_added", "details": "Ask about team structure."},
    )

    assert communication.status_code == 201
    assert note.status_code == 201
    activities = client.get(
        f"/api/v1/applications/{application['id']}/activities",
        headers=account["headers"],
    ).json()
    assert activities[0]["details"] == "Ask about team structure."
    assert activities[1]["details"] == "Recruiter confirmed the next-round schedule."


def test_tracking_rejects_timezone_less_dates_and_enforces_ownership(client, account):
    application = create_application(client, account["headers"])

    invalid = client.post(
        f"/api/v1/applications/{application['id']}/interviews",
        headers=account["headers"],
        json={"round_name": "Screen", "scheduled_at": "2026-10-25T10:00:00"},
    )
    assert invalid.status_code == 422

    null_date = client.post(
        f"/api/v1/applications/{application['id']}/follow-ups",
        headers=account["headers"],
        json={"title": "Reminder", "due_at": None},
    )
    assert null_date.status_code == 422

    scheduled = client.post(
        f"/api/v1/applications/{application['id']}/interviews",
        headers=account["headers"],
        json={
            "round_name": "Screen",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert scheduled.status_code == 201
    null_update = client.patch(
        f"/api/v1/interviews/{scheduled.json()['id']}",
        headers=account["headers"],
        json={"scheduled_at": None},
    )
    assert null_update.status_code == 422

    other_registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "tracking-owner@example.com",
            "display_name": "Other owner",
            "password": "another-long-test-password",
        },
    )
    assert other_registration.status_code == 201
    other_login = client.post(
        "/api/v1/auth/login",
        data={
            "username": "tracking-owner@example.com",
            "password": "another-long-test-password",
        },
    )
    other_headers = {
        "Authorization": f"Bearer {other_login.json()['access_token']}",
    }
    forbidden = client.post(
        f"/api/v1/applications/{application['id']}/follow-ups",
        headers=other_headers,
        json={
            "title": "Unauthorized reminder",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert forbidden.status_code == 404
