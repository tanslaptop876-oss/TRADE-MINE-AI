import json

from app.services.observability_security import (
    ObservabilityAuditJournal,
    redact_sensitive,
)
from app.services.paper_alerts import PaperAlertManager


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
