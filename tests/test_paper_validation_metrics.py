from fastapi.testclient import TestClient

from app.main import app, paper_validation_metrics
from app.services.paper_validation_history import PaperValidationHistory
from app.services.paper_validation_metrics import PaperValidationMetrics


def reset_app_metrics() -> None:
    paper_validation_metrics.history = None
    paper_validation_metrics.history_status = "disabled"
    paper_validation_metrics.total_runs = 0
    paper_validation_metrics.valid_runs = 0
    paper_validation_metrics.invalid_runs = 0
    paper_validation_metrics.recent_issues.clear()
    paper_validation_metrics.recent_runs.clear()


def test_metrics_summary_starts_empty_and_safely_locked():
    metrics = PaperValidationMetrics()

    assert metrics.summary() == {
        "total_runs": 0,
        "valid_runs": 0,
        "invalid_runs": 0,
        "valid_rate": 0.0,
        "recent_issues": [],
        "recent_runs": [],
        "health_status": "insufficient_data",
        "health_threshold": {
            "minimum_runs": 5,
            "minimum_valid_rate": 0.95,
        },
        "history_persistence": {
            "enabled": False,
            "status": "disabled",
        },
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
    assert summary["recent_runs"][-1] == {
        "run_number": 2,
        "valid": False,
        "issue_count": 2,
        "issues": ["bad risk", "bad cash"],
    }


def test_metrics_keeps_only_recent_twenty_issues():
    metrics = PaperValidationMetrics()
    metrics.record({"valid": False, "issues": [f"issue-{i}" for i in range(25)]})

    assert len(metrics.summary()["recent_issues"]) == 20
    assert metrics.summary()["recent_issues"][0] == "issue-5"


def test_metrics_keeps_bounded_recent_run_snapshots():
    metrics = PaperValidationMetrics(max_recent_runs=2)

    metrics.record({"valid": True, "issues": []})
    metrics.record({"valid": False, "issues": ["risk"]})
    metrics.record({"valid": True, "issues": []})

    snapshots = metrics.summary()["recent_runs"]
    assert [snapshot["run_number"] for snapshot in snapshots] == [2, 3]


def test_persistent_history_restores_validation_state(tmp_path):
    history = PaperValidationHistory(tmp_path / "paper-validation.jsonl")
    metrics = PaperValidationMetrics(history=history)
    metrics.record({"valid": True, "issues": []})
    metrics.record({"valid": False, "issues": ["risk"]})

    restored = PaperValidationMetrics(history=history)

    assert restored.total_runs == 2
    assert restored.valid_runs == 1
    assert restored.invalid_runs == 1
    assert restored.history_status == "ok"
    assert restored.history_snapshots(1)[0]["run_number"] == 2


def test_health_status_uses_explicit_sample_and_valid_rate_thresholds():
    healthy = PaperValidationMetrics(
        health_min_runs=3,
        health_valid_rate_threshold=2 / 3,
    )
    healthy.record({"valid": True, "issues": []})
    healthy.record({"valid": False, "issues": ["risk"]})
    assert healthy.health_status() == "insufficient_data"
    healthy.record({"valid": True, "issues": []})
    assert healthy.health_status() == "healthy"

    degraded = PaperValidationMetrics(
        health_min_runs=3,
        health_valid_rate_threshold=0.9,
    )
    for validation in (
        {"valid": True, "issues": []},
        {"valid": True, "issues": []},
        {"valid": False, "issues": ["cash"]},
    ):
        degraded.record(validation)
    assert degraded.health_status() == "degraded"
    assert degraded.alerts()[0]["code"] == "paper_validation_rate_below_threshold"


def test_summary_snapshots_do_not_mutate_internal_history():
    metrics = PaperValidationMetrics()
    metrics.record({"valid": False, "issues": ["risk"]})

    summary = metrics.summary()
    summary["recent_runs"][0]["issues"].append("tampered")

    assert metrics.summary()["recent_runs"][0]["issues"] == ["risk"]


def test_paper_metrics_endpoint_is_read_only_and_reports_dispatch_disabled():
    reset_app_metrics()

    response = TestClient(app).get("/v1/paper/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] == 0
    assert payload["recent_runs"] == []
    assert payload["health_status"] == "insufficient_data"
    assert payload["real_broker_dispatch_enabled"] is False


def test_history_endpoint_is_bounded_and_dispatch_safe():
    reset_app_metrics()
    paper_validation_metrics.record({"valid": True, "issues": []})
    paper_validation_metrics.record({"valid": False, "issues": ["risk"]})

    response = TestClient(app).get("/v1/paper/history?limit=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["runs"][0]["run_number"] == 2
    assert payload["real_broker_dispatch_enabled"] is False


def test_dashboard_exposes_metrics_alerts_and_safety_lock():
    reset_app_metrics()
    paper_validation_metrics.health_min_runs = 1
    paper_validation_metrics.record({"valid": False, "issues": ["risk"]})

    response = TestClient(app).get("/v1/observability/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_alert_count"] == 1
    assert payload["alerts"][0]["status"] == "active"
    assert payload["safety"]["real_broker_dispatch_enabled"] is False


def test_readiness_reports_validation_health_without_enabling_dispatch():
    reset_app_metrics()

    response = TestClient(app).get("/v1/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["paper_validation_health_status"] == "insufficient_data"
    assert payload["real_broker_dispatch_enabled"] is False
