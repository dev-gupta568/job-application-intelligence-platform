from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from app.models.application import JobApplication
from app.models.related import ApplicationActivity, FollowUp, Interview


def test_dashboard_calculates_owned_metrics_and_period_counts(client, account):
    now = datetime.now(timezone.utc)
    today = date.today()

    with client.session_factory() as session:
        user_id = UUID(account["id"])
        applications = {
            status: JobApplication(
                user_id=user_id,
                company_name=f"{status} Company",
                job_title=f"{status} Role",
                status=status,
                applied_on=today,
            )
            for status in ("Interested", "Applied", "Interview", "Offer", "Rejected")
        }
        applications["Future"] = JobApplication(
            user_id=user_id,
            company_name="Future Company",
            job_title="Future Role",
            status="Applied",
            applied_on=today + timedelta(days=1),
        )
        session.add_all(applications.values())
        session.flush()

        session.add_all(
            [
                Interview(
                    application_id=applications["Interview"].id,
                    round_name="Technical",
                    scheduled_at=now + timedelta(days=2),
                ),
                Interview(
                    application_id=applications["Applied"].id,
                    round_name="Completed screen",
                    scheduled_at=now - timedelta(days=2),
                    status="Completed",
                ),
                FollowUp(
                    application_id=applications["Applied"].id,
                    title="Overdue follow-up",
                    due_at=now - timedelta(days=1),
                ),
                FollowUp(
                    application_id=applications["Offer"].id,
                    title="Upcoming follow-up",
                    due_at=now + timedelta(days=3),
                ),
                FollowUp(
                    application_id=applications["Rejected"].id,
                    title="Completed follow-up",
                    due_at=now - timedelta(days=1),
                    completed_at=now,
                ),
                ApplicationActivity(
                    application_id=applications["Offer"].id,
                    event_type="status_changed",
                    previous_status="Applied",
                    new_status="Offer",
                    details="Offer received",
                ),
            ]
        )
        session.commit()

    response = client.get("/api/v1/analytics/dashboard", headers=account["headers"])

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["total_applications"] == 6
    assert dashboard["applied_jobs"] == 2
    assert dashboard["submitted_applications"] == 5
    assert dashboard["interviews_scheduled"] == 1
    assert Decimal(dashboard["interview_conversion_rate"]) == Decimal("40.00")
    assert dashboard["offers_received"] == 1
    assert Decimal(dashboard["offer_conversion_rate"]) == Decimal("20.00")
    assert dashboard["rejected_applications"] == 1
    assert Decimal(dashboard["application_success_rate"]) == Decimal("20.00")
    assert dashboard["status_distribution"] == {
        "Interested": 1,
        "Applied": 2,
        "Assessment": 0,
        "Interview": 1,
        "Offer": 1,
        "Rejected": 1,
        "Withdrawn": 0,
    }
    assert dashboard["weekly_applications"][-1] == {
        "period": (today - timedelta(days=today.weekday())).isoformat(),
        "applications": 4,
    }
    assert dashboard["monthly_applications"][-1] == {
        "period": today.strftime("%Y-%m"),
        "applications": 4,
    }
    assert [item["round_name"] for item in dashboard["upcoming_interviews"]] == ["Technical"]
    follow_ups = {item["title"]: item for item in dashboard["upcoming_follow_ups"]}
    assert follow_ups["Overdue follow-up"]["overdue"] is True
    assert follow_ups["Upcoming follow-up"]["overdue"] is False
    assert "Completed follow-up" not in follow_ups
    assert dashboard["recent_activity"][0]["details"] == "Offer received"


def test_dashboard_is_scoped_to_authenticated_user(client, account):
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": "analytics-owner@example.com",
            "display_name": "Other account",
            "password": "another-long-test-password",
        },
    )
    assert other.status_code == 201
    other_login = client.post(
        "/api/v1/auth/login",
        data={
            "username": "analytics-owner@example.com",
            "password": "another-long-test-password",
        },
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    created = client.post(
        "/api/v1/applications",
        headers=other_headers,
        json={
            "company_name": "Other Company",
            "job_title": "Other Role",
            "status": "Offer",
            "applied_on": date.today().isoformat(),
        },
    )
    assert created.status_code == 201

    response = client.get("/api/v1/analytics/dashboard", headers=account["headers"])

    assert response.status_code == 200
    assert response.json()["total_applications"] == 0
    assert response.json()["offers_received"] == 0
    assert response.json()["application_success_rate"] == "0.00"


def test_empty_dashboard_is_zero_safe_and_requires_authentication(client, account):
    response = client.get("/api/v1/analytics/dashboard", headers=account["headers"])
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["total_applications"] == 0
    assert dashboard["interview_conversion_rate"] == "0.00"
    assert dashboard["application_success_rate"] == "0.00"
    assert all(item["applications"] == 0 for item in dashboard["weekly_applications"])
    assert all(item["applications"] == 0 for item in dashboard["monthly_applications"])

    unauthorized = client.get("/api/v1/analytics/dashboard")
    assert unauthorized.status_code == 401


def test_dashboard_period_limits_are_validated(client, account):
    response = client.get(
        "/api/v1/analytics/dashboard?weeks=0",
        headers=account["headers"],
    )
    assert response.status_code == 422
