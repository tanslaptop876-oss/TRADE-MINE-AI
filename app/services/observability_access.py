from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class ObservabilityAuthMode(str, Enum):
    TRUSTED_NETWORK = "trusted_network"
    OIDC_PROXY = "oidc_proxy"


class ObservabilityAccessError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class ObservabilityIdentity:
    subject: str
    email: str | None
    groups: tuple[str, ...]


class ObservabilityAccessGuard:
    def __init__(
        self,
        *,
        mode: ObservabilityAuthMode = ObservabilityAuthMode.TRUSTED_NETWORK,
        proxy_secret: str | None = None,
        allowed_groups: set[str] | None = None,
    ) -> None:
        self.mode = mode
        self.proxy_secret = proxy_secret
        self.allowed_groups = allowed_groups or set()

    @classmethod
    def from_environment(cls) -> "ObservabilityAccessGuard":
        raw_mode = os.getenv("OBSERVABILITY_AUTH_MODE", "trusted_network")
        try:
            mode = ObservabilityAuthMode(raw_mode)
        except ValueError:
            mode = ObservabilityAuthMode.OIDC_PROXY
        groups = {
            item.strip()
            for item in os.getenv("OBSERVABILITY_ALLOWED_GROUPS", "").split(",")
            if item.strip()
        }
        return cls(
            mode=mode,
            proxy_secret=os.getenv("OBSERVABILITY_PROXY_SHARED_SECRET"),
            allowed_groups=groups,
        )

    def authorize(self, headers: Mapping[str, str]) -> ObservabilityIdentity:
        if self.mode is ObservabilityAuthMode.TRUSTED_NETWORK:
            return ObservabilityIdentity("trusted-network", None, ())

        if not self.proxy_secret:
            raise ObservabilityAccessError(503, "OIDC proxy trust is not configured")
        supplied_secret = headers.get("x-trademind-proxy-secret", "")
        if not hmac.compare_digest(supplied_secret, self.proxy_secret):
            raise ObservabilityAccessError(401, "untrusted authentication proxy")

        subject = headers.get("x-auth-request-user", "").strip()
        if not subject:
            raise ObservabilityAccessError(401, "authenticated identity is missing")
        groups = tuple(
            item.strip()
            for item in headers.get("x-auth-request-groups", "").split(",")
            if item.strip()
        )
        if self.allowed_groups and self.allowed_groups.isdisjoint(groups):
            raise ObservabilityAccessError(403, "observability group access denied")
        return ObservabilityIdentity(
            subject=subject,
            email=headers.get("x-auth-request-email"),
            groups=groups,
        )
