"""
Integration tests for the NudgeOps API.
Requires the backend to be running at http://localhost:8000
Run: pytest tests/integration/ -v
"""
import pytest
import httpx

BASE = "http://localhost:8000/api/v1"
TEST_USER_EXT_ID = "test_integration_user_001"


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=BASE, timeout=10)


@pytest.fixture(scope="module")
def test_user(client):
    # Clean up if exists then create fresh
    r = client.post("/users/", json={
        "external_id": TEST_USER_EXT_ID,
        "display_name": "Integration Test User",
        "email": "integration@test.com"
    })
    if r.status_code == 400:
        # Already exists — find it
        users = client.get("/users/").json()
        for u in users:
            if u["external_id"] == TEST_USER_EXT_ID:
                return u
    assert r.status_code == 201
    return r.json()


class TestHealth:
    def test_root(self, client):
        r = client.get("/", base_url="http://localhost:8000")
        assert r.status_code == 200
        assert "NudgeOps" in r.json()["name"]

    def test_health(self, client):
        r = client.get("/health", base_url="http://localhost:8000")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestUsers:
    def test_create_user(self, test_user):
        assert test_user["external_id"] == TEST_USER_EXT_ID
        assert "id" in test_user

    def test_get_user(self, client, test_user):
        r = client.get(f"/users/{test_user['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == test_user["id"]

    def test_list_users(self, client):
        r = client.get("/users/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_nonexistent_user(self, client):
        r = client.get("/users/nonexistent_id_xyz")
        assert r.status_code == 404


class TestEvents:
    def test_ingest_event(self, client, test_user):
        r = client.post("/events/", json={
            "user_id": test_user["id"],
            "event_type": "session_start",
            "event_source": "test",
            "properties": {"test": True}
        })
        assert r.status_code == 201

    def test_batch_ingest(self, client, test_user):
        r = client.post("/events/batch", json={"events": [
            {"user_id": test_user["id"], "event_type": "task_complete", "event_source": "test"},
            {"user_id": test_user["id"], "event_type": "goal_update", "event_source": "test"},
        ]})
        assert r.status_code == 201
        assert r.json()["ingested"] == 2


class TestBandit:
    def test_get_nudge(self, client, test_user):
        r = client.post("/bandit/nudge", json={"user_id": test_user["id"]})
        assert r.status_code == 200
        data = r.json()
        assert "intervention_type" in data
        assert "message" in data
        assert "log_id" in data
        assert "selection_reason" in data

    def test_submit_feedback(self, client, test_user):
        nudge = client.post("/bandit/nudge", json={"user_id": test_user["id"]}).json()
        r = client.post("/bandit/feedback", json={
            "log_id": nudge["log_id"],
            "user_id": test_user["id"],
            "feedback_signal": "completed"
        })
        assert r.status_code == 200
        assert r.json()["reward"] == 1.0

    def test_invalid_feedback_signal(self, client, test_user):
        nudge = client.post("/bandit/nudge", json={"user_id": test_user["id"]}).json()
        r = client.post("/bandit/feedback", json={
            "log_id": nudge["log_id"],
            "user_id": test_user["id"],
            "feedback_signal": "invalid_signal"
        })
        assert r.status_code == 400

    def test_bandit_state(self, client, test_user):
        r = client.get(f"/bandit/state/{test_user['id']}")
        assert r.status_code == 200
        states = r.json()
        assert len(states) > 0
        for s in states:
            assert "intervention_type" in s
            assert "estimated_success_prob" in s


class TestInterventions:
    def test_list_interventions(self, client):
        r = client.get("/interventions/")
        assert r.status_code == 200
        items = r.json()
        assert len(items) > 0

    def test_intervention_has_required_fields(self, client):
        items = client.get("/interventions/").json()
        for item in items:
            assert "intervention_type" in item
            assert "name" in item
            assert "manipulativeness_score" in item


class TestMonitoring:
    def test_metrics(self, client):
        r = client.get("/monitoring/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "total_interventions_all_time" in data
        assert "alerts" in data

    def test_fairness(self, client):
        r = client.get("/monitoring/fairness")
        assert r.status_code == 200
        data = r.json()
        assert "is_fair" in data
        assert "violations" in data

    def test_health(self, client):
        r = client.get("/monitoring/health")
        assert r.status_code == 200


class TestFeatures:
    def test_get_features(self, client, test_user):
        r = client.get(f"/features/user/{test_user['id']}")
        assert r.status_code == 200
        data = r.json()
        assert "activity_score" in data
        assert "engagement_rate" in data

    def test_compute_embedding(self, client, test_user):
        r = client.post(f"/features/user/{test_user['id']}/embedding")
        assert r.status_code == 200
        data = r.json()
        assert "embedding_dim" in data
        assert data["embedding_dim"] == 32


class TestAudit:
    def test_list_audit_logs(self, client):
        r = client.get("/audit/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
