from fastapi.testclient import TestClient

from app.main import app, paper_validation_metrics
from app.services.paper_validation_metrics import PaperValidationMetrics


def test_metrics_summary_starts_empty_and_safely_locked():
    metrics = PaperValidationMetrics()

    assert metrics.summary() == {
        "total_runs": 0,
        "valid_runs": 0,
        "invalid_runs": 0,
        "valid_rate": 0.0,
        "recent_issues": [],
        "real_broker_dispatch_enabled": False,
    }


def test_metrics_records_valid_and_invalid_runs():
    metrics = PaperValidationMetrics()
    metrics.record({"valid": True, "issues": []})
    metrics.record({"valid": False, "issues": ["bad risk", "bad cash"]})

    summary = metrics.summary()
    assert summary["total_runs"] == 2
    assert summary["valid_runs"] == 1
    assert summary["invalid_runs"] == 1
    assert summary["valid_rate"] == 0.5
    assert summary["recent_issues"] == ["bad risk", "bad cash"]


def test_metrics_keeps_only_recent_twenty_issues():
    metrics = PaperValidationMetrics()
    metrics.record({"valid": False, "issues": [f"issue-{i}" for i in range(25)]})

    assert len(metrics.summary()["recent_issues"]) == 20
    assert metrics.summary()["recent_issues"][0] == "issue-5"


def test_paper_metrics_endpoint_is_read_only_and_reports_dispatch_disabled():
    paper_validation_metrics.total_runs = 0
    paper_validation_metrics.valid_runs = 0
    paper_validation_metrics.invalid_runs = 0
    paper_validation_metrics.recent_issues.clear()

    response = TestClient(app).get("/v1/paper/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] == 0
    assert payload["real_broker_dispatch_enabled"] is False
