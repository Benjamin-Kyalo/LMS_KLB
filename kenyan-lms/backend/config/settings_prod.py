"""Production settings.

Select with::

    DJANGO_SETTINGS_MODULE=config.settings_prod python manage.py check --deploy

These settings deliberately fail fast if the operator has not configured
hosts and CORS origins. They do not deploy anything by themselves; a real
web server, TLS termination and a process manager are still required.
"""
from .settings import *  # noqa: F401,F403 - inherit the shared configuration

# Fail closed: a forgotten host list must never expose the service.
DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=CORS_ALLOWED_ORIGINS)

# TLS / reverse-proxy settings. The proxy must set X-Forwarded-Proto: https.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # the SPA reads the token for its forms
CSRF_COOKIE_SAMESITE = "Lax"

# Keep request bodies bounded; uploads use media storage, not request memory.
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024)
FILE_UPLOAD_MAX_MEMORY_SIZE = env.int("FILE_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024)

EMAIL_SUBJECT_PREFIX = "[KLB LMS] "

# The inherited MAILERS entry may be the console backend when the developer's
# .env has DEBUG=True. Production must always send real email.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": SMTP_HOST,
            "port": SMTP_PORT,
            "username": SMTP_USER,
            "password": SMTP_PASSWORD,
            "use_tls": SMTP_USE_TLS,
            "use_ssl": SMTP_USE_SSL,
            "timeout": SMTP_TIMEOUT,
            "fail_silently": False,
        },
    }
}
