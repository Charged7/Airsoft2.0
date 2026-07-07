import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw_value = os.getenv(name, default)

    return [
        item.strip()
        for item in raw_value.replace("\n", ",").split(",")
        if item.strip()
    ]

# SECURITY

load_dotenv()

DEBUG = env_bool("DEBUG", False)
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "unsafe-local-development-key"
    else:
        raise RuntimeError("SECRET_KEY is required when DEBUG=False.")

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost",
)

render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")

if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

if env_bool("RENDER", False) and ".onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")

# APPLICATIONS

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",

    # Local apps
    "picker",
]

# MIDDLEWARE

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# TEMPLATES
# Поки залишаємо, навіть якщо проєкт API-only

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

# DATABASE

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
    }
}

# PASSWORDS

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# INTERNATIONALIZATION

LANGUAGE_CODE = "uk"

TIME_ZONE = "Europe/Kyiv"

USE_I18N = True
USE_TZ = True

# STATIC

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# MEDIA

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# DEFAULT PRIMARY KEY

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],

    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination.PageNumberPagination",

    "PAGE_SIZE": 20,
}

# CORS

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", False)

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
