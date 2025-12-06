"""
Django production settings.
"""

from typing import Any, cast

from .base import *  # noqa: F401, F403
from .base import LOGGING as _LOGGING

DEBUG = False

# Security settings
CSRF_TRUSTED_ORIGINS = ["https://mkofoed.dev", "https://www.mkofoed.dev"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# WhiteNoise compression and caching
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Production logging - Sentry captures logs via enable_logs=True in sentry_sdk.init()
# Console also shows INFO+ for Docker logs visibility
LOGGING = cast(dict[str, Any], _LOGGING)
LOGGING["handlers"] = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "simple",
        "level": "INFO",  # Show INFO and above in console
    },
}
LOGGING["root"]["level"] = "INFO"  # type: ignore[index]
LOGGING["loggers"]["django"]["level"] = "INFO"  # type: ignore[index]
