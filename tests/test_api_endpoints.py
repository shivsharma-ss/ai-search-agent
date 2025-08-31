from fastapi.testclient import TestClient

from ai_search_agent.api import app


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_test_settings_preflight_ok(monkeypatch):
    # Force preflight to return ok without performing network calls
    from ai_search_agent import api as api_mod

    def fake_preflight(**kwargs):
        return {
            "ok": True,
            "openai": {"ok": True, "message": "ok"},
            "brightdata_api": {"ok": True, "message": "ok"},
            "reddit_dataset": {"ok": True, "message": "ok"},
            "reddit_comments_dataset": {"ok": True, "message": "ok"},
        }

    monkeypatch.setattr(api_mod, "preflight_check", fake_preflight)
    c = TestClient(app)
    r = c.post(
        "/api/test-settings",
        json={
            "openai_api_key": "x",
            "brightdata_api_key": "y",
            "reddit_dataset_id": "gd_abc",
            "reddit_comments_dataset_id": "gd_def",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["brightdata_ok"] is True


def test_research_sanitizes_non_serializable(monkeypatch):
    # Return a result that includes a non-serializable field to ensure
    # the API filters only allowed, JSON-safe keys.
    from ai_search_agent import api as api_mod

    def fake_run_research(question, config=None, openai_api_key=None):
        class NotJSON:
            pass

        return {
            "final_answer": "It depends",
            "messages": [NotJSON()],  # should be dropped by API
            "google_results": {"organic": []},
        }

    def fake_preflight(**kwargs):
        return {
            "ok": True,
            "openai": {"ok": True},
            "brightdata_api": {"ok": True},
            "reddit_dataset": {"ok": True},
            "reddit_comments_dataset": {"ok": True},
        }

    monkeypatch.setattr(api_mod, "run_research", fake_run_research)
    monkeypatch.setattr(api_mod, "preflight_check", fake_preflight)

    c = TestClient(app)
    r = c.post(
        "/api/research",
        json={
            "question": "Is TypeScript worth it?",
            "openai_api_key": "x",
            "brightdata_api_key": "y",
            "reddit_dataset_id": "gd_abc",
            "reddit_comments_dataset_id": "gd_def",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["final_answer"] == "It depends"
    assert "messages" not in data
