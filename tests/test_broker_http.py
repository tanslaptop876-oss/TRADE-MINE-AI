from app.services.broker_http import IciciSessionTransport, UpstoxAuthTransport


class FakeResponse:
    ok = True
    status_code = 200

    def json(self):
        return {"access_token": "test-token"}


def test_upstox_code_exchange_uses_oauth_contract():
    captured = {}

    def fake_request(method, url, **kwargs):
        captured.update({"method": method, "url": url, **kwargs})
        return FakeResponse()

    result = UpstoxAuthTransport(fake_request).exchange_code(
        code="auth-code",
        client_id="client",
        client_secret="secret",
        redirect_uri="https://example.test/callback",
    )

    assert result.ok is True
    assert result.data["access_token"] == "test-token"
    assert captured["method"] == "POST"
    assert captured["data"]["grant_type"] == "authorization_code"
    assert captured["timeout"] == 10


def test_icici_session_transport_delegates_to_supported_client():
    captured = {}

    def fake_factory(**kwargs):
        captured.update(kwargs)
        return {"session_token": "test-session"}

    result = IciciSessionTransport(fake_factory).create_session(
        app_key="app",
        client_secret="secret",
        user_id="user",
        api_session="api-session",
    )

    assert result["session_token"] == "test-session"
    assert captured["user_id"] == "user"


def test_icici_session_rejects_incomplete_credentials():
    transport = IciciSessionTransport(lambda **kwargs: kwargs)

    try:
        transport.create_session(
            app_key="app",
            client_secret="",
            user_id="user",
            api_session="session",
        )
    except ValueError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("expected incomplete ICICI credentials to be rejected")
