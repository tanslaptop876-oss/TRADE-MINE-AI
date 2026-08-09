from pathlib import Path


def test_render_staging_is_free_and_oidc_fail_closed():
    blueprint = Path("render.yaml").read_text(encoding="utf-8")

    assert "plan: free" in blueprint
    assert "healthCheckPath: /health" in blueprint
    assert "OBSERVABILITY_AUTH_MODE" in blueprint
    assert "value: oidc_proxy" in blueprint
    assert "generateValue: true" in blueprint
    assert "real_broker_dispatch_enabled" not in blueprint


def test_container_runs_unprivileged_and_binds_render_port():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "USER appuser" in dockerfile
    assert "--host 0.0.0.0" in dockerfile
    assert "${PORT:-10000}" in dockerfile
