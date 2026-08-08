from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services.paper_alerts import PaperAlertJournal, PaperAlertManager
from app.services.paper_validation_metrics import PaperValidationMetrics


ALERT = {
    "code": "paper_validation_rate_below_threshold",
    "severity": "warning",
    "status": "active",
    "message": "valid rate is low",
}


def test_alert_manager_deduplicates_and_acknowledges_persistently(tmp_path):
    journal = PaperAlertJournal(tmp_path / "alerts.json")
    manager = PaperAlertManager(journal=journal)

    current = manager.current([ALERT, ALERT], current_run=10)
    assert len(current) == 1
    assert current[0]["status"] == "active"

    manager.acknowledge(ALERT["code"], current_run=10)
    restored = PaperAlertManager(journal=journal)

    assert restored.current([ALERT], current_run=10)[0]["status"] == "acknowledged"
    assert restored.outbound_delivery_enabled is False


def test_resolved_alert_is_suppressed_until_cooldown_expires():
    manager = PaperAlertManager(cooldown_runs=3)
    manager.resolve(ALERT["code"], current_run=5)

    assert manager.current([ALERT], current_run=7) == []
    assert manager.current([ALERT], current_run=8)[0]["status"] == "active"


def test_alert_lifecycle_api_is_dispatch_safe(monkeypatch):
    metrics = PaperValidationMetrics(
        health_min_runs=1,
        health_valid_rate_threshold=1.0,
    )
    metrics.record({"valid": False, "issues": ["risk"]})
    manager = PaperAlertManager(cooldown_runs=5)
    monkeypatch.setattr(main_module, "paper_validation_metrics", metrics)
    monkeypatch.setattr(main_module, "paper_alert_manager", manager)
    client = TestClient(app)
    code = "paper_validation_rate_below_threshold"

    acknowledged = client.post(
        f"/v1/observability/alerts/{code}/acknowledge"
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["outbound_delivery_enabled"] is False
    assert acknowledged.json()["real_broker_dispatch_enabled"] is False

    resolved = client.post(f"/v1/observability/alerts/{code}/resolve")
    assert resolved.status_code == 200
    alerts = client.get("/v1/observability/alerts").json()
    assert alerts["alerts"] == []
    assert alerts["outbound_delivery_enabled"] is False
    assert alerts["real_broker_dispatch_enabled"] is False
