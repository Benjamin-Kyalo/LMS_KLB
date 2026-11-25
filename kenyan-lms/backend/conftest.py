"""Test-only settings. Production password hashing is unchanged."""


def pytest_configure():
    from django.conf import settings

    # The suite creates many users per test. A fast, deterministic hasher keeps
    # verification practical while still exercising real password checks.
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
