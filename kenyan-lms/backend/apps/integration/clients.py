"""Environment-only OneRoster client registry and HS256 assertion checks.

This module deliberately uses only the Python standard library. It supports
short-lived HS256 bearer assertions, not LTI 1.3, OIDC discovery, JWKS, RS256
or an OAuth token endpoint. Client secrets are read from ``KLB_ONEROSTER_CLIENTS``
in the server environment and are never serialised or returned by the API.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings

DEFAULT_AUDIENCE = "klb-lms-oneroster"
ALLOWED_ALGORITHM = "HS256"
CLOCK_SKEW_SECONDS = 30


@dataclass(frozen=True)
class OneRosterClient:
    """One pinned external client, configured only in the server environment."""

    client_id: str
    secret: str
    institution_id: int
    scopes: frozenset[str]


@dataclass(frozen=True)
class OneRosterPrincipal:
    """The authenticated caller for a read-only OneRoster request."""

    client_id: str
    institution_id: int
    scopes: frozenset[str]
    is_authenticated: bool = True
    is_anonymous: bool = False

    def __str__(self):
        return self.client_id


def configured_clients() -> dict[str, OneRosterClient]:
    """Parse and validate the env-driven client map.

    Expected shape::

        {"client-id": {"secret": "...", "institution_id": 1,
                       "scopes": ["courses.read", ...]}}

    Invalid entries are skipped so one bad row cannot disable every client.
    """
    raw = getattr(settings, "ONEROSTER_CLIENTS_JSON", "") or ""
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(parsed, dict):
        return {}

    clients: dict[str, OneRosterClient] = {}
    for raw_id, raw_config in parsed.items():
        client_id = str(raw_id or "").strip()
        if not client_id or not isinstance(raw_config, dict):
            continue
        secret = str(raw_config.get("secret") or "").strip()
        institution_id = raw_config.get("institution_id")
        scopes = raw_config.get("scopes")
        if not secret or not isinstance(scopes, (list, tuple)):
            continue
        try:
            institution_id = int(institution_id)
        except (TypeError, ValueError):
            continue
        if institution_id <= 0:
            continue
        clean_scopes = frozenset(str(scope).strip() for scope in scopes if str(scope).strip())
        if not clean_scopes:
            continue
        clients[client_id] = OneRosterClient(
            client_id=client_id,
            secret=secret,
            institution_id=institution_id,
            scopes=clean_scopes,
        )
    return clients


def get_client(client_id: str) -> OneRosterClient | None:
    return configured_clients().get(str(client_id or "").strip())


def _decode_segment(segment: str) -> Any:
    padded = segment + "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def _decode_signature(segment: str) -> bytes:
    padded = segment + "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def decode_assertion(token: str) -> tuple[OneRosterPrincipal, dict] | None:
    """Return a principal for a valid HS256 assertion, otherwise ``None``.

    Every failure is collapsed into ``None`` so callers cannot distinguish a
    bad signature from an unsupported algorithm. That keeps the API response
    short and gives an attacker no configuration hints.
    """
    if not isinstance(token, str):
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_part, payload_part, signature_part = parts
    try:
        header = _decode_segment(header_part)
        claims = _decode_segment(payload_part)
        signature = _decode_signature(signature_part)
    except (ValueError, UnicodeDecodeError, binascii.Error, TypeError):
        return None
    if not isinstance(header, dict) or not isinstance(claims, dict):
        return None
    # RS256, none and any other value are refused here; there is no JWKS or
    # public-key path in this groundwork.
    if header.get("alg") != ALLOWED_ALGORITHM:
        return None
    if header.get("typ") not in (None, "JWT"):
        return None

    client_id = str(claims.get("iss") or claims.get("sub") or "").strip()
    client = get_client(client_id)
    if client is None:
        return None
    if claims.get("sub") not in (None, client_id):
        return None

    expected_audience = getattr(settings, "ONEROSTER_AUDIENCE", DEFAULT_AUDIENCE)
    audience = claims.get("aud")
    if isinstance(audience, (list, tuple)):
        if expected_audience not in audience:
            return None
    elif audience != expected_audience:
        return None

    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    expected_signature = hmac.new(
        client.secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    now = time.time()
    try:
        issued_at = float(claims["iat"])
        expires_at = float(claims["exp"])
    except (KeyError, TypeError, ValueError):
        return None
    if expires_at <= issued_at or expires_at <= now - CLOCK_SKEW_SECONDS:
        return None
    if issued_at > now + CLOCK_SKEW_SECONDS:
        return None
    not_before = claims.get("nbf")
    if not_before is not None:
        try:
            if float(not_before) > now + CLOCK_SKEW_SECONDS:
                return None
        except (TypeError, ValueError):
            return None
    max_ttl = int(getattr(settings, "ONEROSTER_TOKEN_TTL_SECONDS", 300))
    if expires_at - issued_at > max_ttl + CLOCK_SKEW_SECONDS:
        return None
    if claims.get("jti") is not None and not isinstance(claims["jti"], str):
        return None

    return (
        OneRosterPrincipal(
            client_id=client.client_id,
            institution_id=client.institution_id,
            scopes=client.scopes,
        ),
        claims,
    )
