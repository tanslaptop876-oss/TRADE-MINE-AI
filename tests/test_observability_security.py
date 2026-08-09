from fastapi.testclient import TestClient

from app.main import app
import json

from app.services.observability_security import (
    ObservabilityAuditJournal,
    redact_sensitive,
)
from app.services.paper_alerts import PaperAlertManager
from app.services.paper_validation_history import PaperValidationHistory


def test_sensitive_fields_are_recursively_redacted():
    payload = {
        "token": "top-secret",
        "nested": {
            "password": "hidden",
            "safe": "visible",
        },
        "items": [{"api_key": "private"}],
    }

    assert redact_sensitive(payload) == {
        "token": "[REDACTED]",
        "nested": {
            "password": "[REDACTED]",
            "safe": "visible",
        },
        "items": [{"api_key": "[REDACTED]"}],
    }


def test_audit_journal_redacts_and_recovers_from_malformed_lines(tmp_path):
    path = tmp_path / "audit.jsonl"
    journal = ObservabilityAuditJournal(path)
    journal.append(
        "test_event",
        {"token": "secret-value", "safe": "visible"},
    )
    with path.open("a", encoding="utf-8") as audit_file:
        audit_file.write("not-json\n")

    events = journal.recent()

    assert len(events) == 1
    assert events[0]["event_type"] == "test_event"
    assert events[0]["details"]["token"] == "[REDACTED]"
    assert events[0]["details"]["safe"] == "visible"
    assert "secret-value" not in path.read_text(encoding="utf-8")


def test_alert_lifecycle_emits_structured_audit_events(tmp_path):
    journal = ObservabilityAuditJournal(tmp_path / "audit.jsonl")
    manager = PaperAlertManager(audit_journal=journal)

    manager.acknowledge("validation_low", current_run=4)
    manager.resolve("validation_low", current_run=5)

    events = journal.recent()
    assert [event["event_type"] for event in events] == [
        "paper_alert_acknowledged",
        "paper_alert_resolved",
    ]
    assert events[-1]["details"] == {
        "code": "validation_low",
        "current_run": 5,
    }
    assert manager.audit_status == "ok"
    assert manager.outbound_delivery_enabled is False


def test_audit_lines_remain_valid_json(tmp_path):
    journal = ObservabilityAuditJournal(tmp_path / "audit.jsonl")
    journal.append("event", {"safe": True})

    line = journal.path.read_text(encoding="utf-8").strip()
    assert json.loads(line)["details"] == {"safe": True}


def test_history_lifecycle_emits_append_compaction_and_recovery_events(tmp_path):
    audit = ObservabilityAuditJournal(tmp_path / "audit.jsonl")
    history_path = tmp_path / "history.jsonl"
    history = PaperValidationHistory(
        history_path,
        max_records=1,
        audit_journal=audit,
    )

    history.append({"run_number": 1, "valid": True, "issues": []})
    history.append({"run_number": 2, "valid": False, "issues": ["risk"]})
    history_path.write_text("corrupt-primary\n", encoding="utf-8")
    recovered = history.load()

    event_types = [event["event_type"] for event in audit.recent()]
    assert event_types.count("paper_validation_history_appended") == 2
    assert "paper_validation_history_compacted" in event_types
    assert "paper_validation_history_recovered" in event_types
    assert [record["run_number"] for record in recovered] == [1, 2]
    assert history.audit_status == "ok"


def test_history_audit_failure_does_not_block_persistence(tmp_path):
    class FailingAuditJournal:
        def append(self, event_type, details):
            raise OSError("audit unavailable")

    history = PaperValidationHistory(
        tmp_path / "history.jsonl",
        audit_journal=FailingAuditJournal(),
    )

    history.append({"run_number": 1, "valid": True, "issues": []})

    assert history.load()[0]["run_number"] == 1
    assert history.audit_status == "error"


def test_storage_diagnostics_report_counts_without_exposing_paths(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    audit = ObservabilityAuditJournal(audit_path)
    audit.append("event", {"safe": True})
    with audit_path.open("a", encoding="utf-8") as audit_file:
        audit_file.write("not-json\n")

    history_path = tmp_path / "history.jsonl"
    history = PaperValidationHistory(history_path, max_records=1)
    history.append({"run_number": 1, "valid": True, "issues": []})
    history.append({"run_number": 2, "valid": True, "issues": []})
    history_path.write_text("corrupt-primary\n", encoding="utf-8")

    audit_diagnostics = audit.diagnostics()
    history_diagnostics = history.diagnostics()

    assert audit_diagnostics["valid_record_count"] == 1
    assert audit_diagnostics["malformed_record_count"] == 1
    assert audit_diagnostics["status"] == "degraded"
    assert history_diagnostics["backup_recovery_active"] is True
    assert history_diagnostics["valid_record_count"] == 2
    assert history_diagnostics["retention"]["max_records"] == 1
    assert "path" not in audit_diagnostics
    assert "path" not in history_diagnostics


def test_storage_diagnostics_endpoint_is_read_only_and_dispatch_safe():
    response = TestClient(app).get("/v1/observability/storage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["outbound_delivery_enabled"] is False
    assert payload["real_broker_dispatch_enabled"] is False
    assert set(payload["history"]) >= {
        "status",
        "valid_record_count",
        "malformed_record_count",
        "retention",
    }
    assert set(payload["audit"]) >= {
        "status",
        "valid_record_count",
        "malformed_record_count",
    }
