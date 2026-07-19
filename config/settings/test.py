"""Settings for the isolated automated test suite."""

from .base import *  # noqa: F401, F403
from .base import MIDDLEWARE as BASE_MIDDLEWARE

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MIGRATION_MODULES = {
    "blog": None,
    "core": None,
    "dashboard": None,
    "showcase": None,
    "visitors": None,
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True
MIDDLEWARE = [
    middleware for middleware in BASE_MIDDLEWARE if middleware != "visitors.middleware.VisitorTrackingMiddleware"
]
