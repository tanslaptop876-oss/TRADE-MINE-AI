from fastapi.testclient import TestClient

from app.main import app, observability_access_guard
from app.services.observability_access import (
    ObservabilityAccessError,
    ObservabilityAccessGuard,
    ObservabilityAuthMode,
)


def test_oidc_proxy_mode_fails_closed_without_trust_secret():
    guard = ObservabilityAccessGuard(mode=ObservabilityAuthMode.OIDC_PROXY)

    try:
        guard.authorize({"x-auth-request-user": "user@example.com"})
    except ObservabilityAccessError as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("missing proxy trust must fail closed")


def test_oidc_proxy_rejects_spoofed_proxy_and_missing_identity():
    guard = ObservabilityAccessGuard(
        mode=ObservabilityAuthMode.OIDC_PROXY,
        proxy_secret="proxy-secret",
    )

    for headers in (
        {"x-trademind-proxy-secret": "wrong", "x-auth-request-user": "user"},
        {"x-trademind-proxy-secret": "proxy-secret"},
    ):
        try:
            guard.authorize(headers)
        except ObservabilityAccessError as exc:
            assert exc.status_code == 401
        else:
            raise AssertionError("invalid proxy identity must be rejected")


def test_oidc_proxy_enforces_group_allowlist():
    guard = ObservabilityAccessGuard(
        mode=ObservabilityAuthMode.OIDC_PROXY,
        proxy_secret="proxy-secret",
        allowed_groups={"trademind-observers"},
    )

    identity = guard.authorize(
        {
            "x-trademind-proxy-secret": "proxy-secret",
            "x-auth-request-user": "alice",
            "x-auth-request-email": "alice@example.com",
            "x-auth-request-groups": "staff,trademind-observers",
        }
    )
    assert identity.subject == "alice"
    assert identity.email == "alice@example.com"

    try:
        guard.authorize(
            {
                "x-trademind-proxy-secret": "proxy-secret",
                "x-auth-request-user": "bob",
                "x-auth-request-groups": "staff",
            }
        )
    except ObservabilityAccessError as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("non-allowlisted group must be rejected")


def test_observability_endpoint_uses_fail_closed_oidc_proxy_mode():
    original_mode = observability_access_guard.mode
    original_secret = observability_access_guard.proxy_secret
    original_groups = observability_access_guard.allowed_groups
    try:
        observability_access_guard.mode = ObservabilityAuthMode.OIDC_PROXY
        observability_access_guard.proxy_secret = "proxy-secret"
        observability_access_guard.allowed_groups = {"observers"}
        client = TestClient(app)

        assert client.get("/v1/observability/storage").status_code == 401
        response = client.get(
            "/v1/observability/access",
            headers={
                "x-trademind-proxy-secret": "proxy-secret",
                "x-auth-request-user": "alice",
                "x-auth-request-groups": "observers",
            },
        )
        assert response.status_code == 200
        assert response.json()["authenticated"] is True
        assert response.json()["real_broker_dispatch_enabled"] is False
    finally:
        observability_access_guard.mode = original_mode
        observability_access_guard.proxy_secret = original_secret
        observability_access_guard.allowed_groups = original_groups
