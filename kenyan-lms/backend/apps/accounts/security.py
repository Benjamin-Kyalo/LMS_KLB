"""Helpers for sign-in throttling and one-time reset tokens."""
import hashlib
import math

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

from apps.accounts.models import LoginAttempt


def client_ip(request):
    """Trust X-Forwarded-For only when the direct peer is a configured proxy."""
    remote = (request.META.get("REMOTE_ADDR") or "unknown")[:64]
    trusted = getattr(settings, "TRUSTED_PROXY_IPS", [])
    if remote not in trusted:
        return remote
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:64] or remote
    return remote


def normalise_key(value):
    return (value or "").strip().lower()[:150] or "unknown"


def _attempts_for(request, key):
    """Track both the IP/username pair and a global username counter."""
    normalised = normalise_key(key)
    scopes = [(client_ip(request), normalised), ("username", normalised)]
    return [
        LoginAttempt.objects.get_or_create(ip_address=ip, username=name)[0]
        for ip, name in scopes
    ]


def assert_login_allowed(request, username):
    """Reject a locked scope and clear expired locks."""
    now = timezone.now()
    for attempt in _attempts_for(request, username):
        if not attempt.locked_until:
            continue
        if attempt.locked_until > now:
            minutes = max(1, math.ceil((attempt.locked_until - now).total_seconds() / 60))
            raise ValidationError({
                "detail": f"Too many sign-in attempts. Try again in {minutes} minutes."
            })
        attempt.failed_count = 0
        attempt.first_failed_at = None
        attempt.last_failed_at = None
        attempt.locked_until = None
        attempt.save(update_fields=[
            "failed_count", "first_failed_at", "last_failed_at", "locked_until"
        ])


def record_failed_login(request, username):
    """Count a failed sign-in and lock the scopes when the limit is reached."""
    now = timezone.now()
    for attempt in _attempts_for(request, username):
        attempt.failed_count += 1
        if attempt.first_failed_at is None:
            attempt.first_failed_at = now
        attempt.last_failed_at = now
        if attempt.failed_count >= settings.LOGIN_FAIL_MAX:
            attempt.locked_until = now + timezone.timedelta(
                seconds=settings.LOGIN_LOCKOUT_SECONDS
            )
        attempt.save(update_fields=[
            "failed_count", "first_failed_at", "last_failed_at", "locked_until"
        ])


def record_successful_login(request, username):
    """Clear both counters after a genuine sign-in."""
    LoginAttempt.objects.filter(
        ip_address=client_ip(request), username=normalise_key(username)
    ).delete()
    LoginAttempt.objects.filter(
        ip_address="username", username=normalise_key(username)
    ).delete()


def reset_request_key(email):
    """Keep reset abuse counters separate from password sign-in counters."""
    return "reset:" + normalise_key(email)


def reset_request_count(request, email):
    """Count recent reset requests without locking a legitimate user out."""
    key = reset_request_key(email)
    window_start = timezone.now() - timezone.timedelta(
        seconds=settings.RESET_REQUEST_WINDOW_SECONDS
    )
    attempt = LoginAttempt.objects.filter(
        ip_address=client_ip(request), username=key
    ).first()
    if not attempt or not attempt.last_failed_at or attempt.last_failed_at < window_start:
        return 0
    return attempt.failed_count


def record_reset_request(request, email):
    """Record a reset request in a rolling window, never as a login failure."""
    key = reset_request_key(email)
    now = timezone.now()
    window_start = now - timezone.timedelta(seconds=settings.RESET_REQUEST_WINDOW_SECONDS)
    attempt, _ = LoginAttempt.objects.get_or_create(
        ip_address=client_ip(request), username=key
    )
    if not attempt.last_failed_at or attempt.last_failed_at < window_start:
        attempt.failed_count = 0
        attempt.first_failed_at = now
    attempt.failed_count += 1
    attempt.last_failed_at = now
    attempt.locked_until = None
    attempt.save(update_fields=[
        "failed_count", "first_failed_at", "last_failed_at", "locked_until"
    ])
    return attempt.failed_count


def hash_reset_token(token):
    """Store only a digest of a spent reset token, never the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def invalidate_user_sessions(user, keep_session_key=None):
    """Sign out other browser sessions and revoke legacy API tokens."""
    Token.objects.filter(user=user).delete()
    store = SessionStore()
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        if keep_session_key and session.session_key == keep_session_key:
            continue
        try:
            # Django 6.x made decode() an instance method, so use a store
            # instance rather than calling the class directly.
            data = store.decode(session.session_data)
        except Exception:
            # A session signed with an older key cannot be attributed to this
            # user. Deleting it would sign out someone else (and can break the
            # current request with SessionInterrupted), so leave it alone.
            continue
        if str(data.get("_auth_user_id") or "") == str(user.pk):
            session.delete()
