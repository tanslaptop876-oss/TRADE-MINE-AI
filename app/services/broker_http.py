from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


JsonRequest = Callable[..., Any]


@dataclass(frozen=True)
class BrokerHttpResult:
    ok: bool
    status_code: int
    data: Mapping[str, Any]


class UpstoxAuthTransport:
    token_url = "https://api.upstox.com/v2/login/authorization/token"

    def __init__(self, request: JsonRequest):
        self.request = request

    def exchange_code(
        self,
        *,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> BrokerHttpResult:
        response = self.request(
            "POST",
            self.token_url,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        payload = response.json()
        return BrokerHttpResult(response.ok, response.status_code, payload)


class IciciSessionTransport:
    """Boundary for ICICI Direct session creation.

    ICICI session creation is intentionally injected rather than hard-wired to
    an unofficial endpoint. The production caller can wrap the broker's
    supported SDK/session client while tests use a fake callable.
    """

    def __init__(self, session_factory: Callable[..., Mapping[str, Any]]):
        self.session_factory = session_factory

    def create_session(
        self,
        *,
        app_key: str,
        client_secret: str,
        user_id: str,
        api_session: str,
    ) -> Mapping[str, Any]:
        if not all(value.strip() for value in (app_key, client_secret, user_id, api_session)):
            raise ValueError("ICICI session credentials are incomplete")
        return self.session_factory(
            app_key=app_key,
            client_secret=client_secret,
            user_id=user_id,
            api_session=api_session,
        )
