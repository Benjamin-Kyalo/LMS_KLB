"""
Django settings for the Kenyan Digital Learning Ecosystem.

All secrets come from the .env file at the project root. No password is
ever written in this file. See .env.example for the required keys.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

env = environ.Env()
env.read_env(PROJECT_ROOT / ".env")

# Logging writes to this folder, so make sure it exists on a fresh checkout.
(BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.institutions",
    "apps.learners",
    "apps.teachers",
    "apps.guardians",
    "apps.academics",
    "apps.attendance",
    "apps.curriculum",
    "apps.courses",
    "apps.assessments",
    "apps.content",
    "apps.communications",
    "apps.reports",
    "apps.fees",
    "apps.approval",
    "apps.kemis",
    "apps.tutor",
    "apps.analytics",
    "apps.theming",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "apps.core.middleware.TrustedProxyHeaderMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"connect_timeout": 10},
    }
}

AUTH_USER_MODEL = "accounts.User"
# Django's default PBKDF2 hasher is deliberately retained. It is salted,
# adaptive and requires no extra native dependency. Do not weaken it.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", default=60 * 60)

# The SPA uses Django's session cookie, which stays HttpOnly. The CSRF cookie
# is readable by JavaScript so the API layer can echo it in X-CSRFToken.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=60 * 60 * 2)
SESSION_EXPIRE_AT_BROWSER_CLOSE = env.bool("SESSION_EXPIRE_AT_BROWSER_CLOSE", default=True)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://127.0.0.1:5173", "http://localhost:5173"],
)

# Brute-force protection: lock an IP/username pair after repeated failures.
LOGIN_FAIL_MAX = env.int("LOGIN_FAIL_MAX", default=5)
LOGIN_LOCKOUT_SECONDS = env.int("LOGIN_LOCKOUT_SECONDS", default=15 * 60)
# Never trust X-Forwarded-For unless the direct peer is a known reverse proxy.
TRUSTED_PROXY_IPS = env.list("TRUSTED_PROXY_IPS", default=[])
# Reset emails must link to the frontend origin, not the API host.
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="")
# Supply a shared Redis URL when running more than one worker so throttles and
# lockouts are shared. Django's default local-memory cache is per-process.
CACHE_URL = env("CACHE_URL", default="")
if CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": CACHE_URL,
        }
    }
RESET_REQUEST_MAX = env.int("RESET_REQUEST_MAX", default=5)
RESET_REQUEST_WINDOW_SECONDS = env.int("RESET_REQUEST_WINDOW_SECONDS", default=60 * 60)

LANGUAGE_CODE = "en-ke"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Optimistic updates need a structured conflict instead of an opaque 500.
    "EXCEPTION_HANDLER": "apps.core.concurrency.conflict_exception_handler",
}

# Deliberately generous defaults: these supplement the explicit login and
# reset lockouts, not replace them. Operators can tighten them per deployment.
DEFAULT_THROTTLE_RATES = {
    "auth_login": env("LOGIN_THROTTLE_RATE", default="100/hour"),
    "auth_register": env("REGISTER_THROTTLE_RATE", default="20/hour"),
    "auth_reset": env("RESET_THROTTLE_RATE", default="20/hour"),
    "tutor_ask": env("TUTOR_THROTTLE_RATE", default="120/hour"),
    "export_generate": env("EXPORT_THROTTLE_RATE", default="60/hour"),
}

# Production overrides this through config/settings_prod.py. Keeping an empty
# default means local development is not blocked by an enforce-only policy.
SECURITY_HEADERS = {}

# Local-first uploads stay modest by default. Deployments handling large local
# video files must raise this together with DATA_UPLOAD_MAX_MEMORY_SIZE and
# FILE_UPLOAD_MAX_MEMORY_SIZE in config/settings_prod.py.
CONTENT_RESOURCE_MAX_UPLOAD_BYTES = env.int(
    "CONTENT_RESOURCE_MAX_UPLOAD_BYTES", default=5 * 1024 * 1024,
)

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True

# Django 6.1 uses MAILERS. Defining the old EMAIL_* settings triggers a
# deprecation warning, so SMTP values are read into neutral variable names.
SMTP_HOST = env("SMTP_HOST", default="")
SMTP_PORT = env.int("SMTP_PORT", default=587)
SMTP_USER = env("SMTP_USER", default="")
SMTP_PASSWORD = env("SMTP_PASSWORD", default="")
SMTP_USE_TLS = env.bool("SMTP_USE_TLS", default=True)
SMTP_USE_SSL = env.bool("SMTP_USE_SSL", default=False)
SMTP_TIMEOUT = env.int("SMTP_TIMEOUT", default=20)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="KLB LMS <no-reply@klb.local>")

if DEBUG:
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.console.EmailBackend",
            "OPTIONS": {},
        }
    }
else:
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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "lms.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "simple",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}
