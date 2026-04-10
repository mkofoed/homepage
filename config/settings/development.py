"""
Django development settings.
"""
from typing import Any, cast

from .base import *  # noqa: F401, F403
from .base import LOGGING as _LOGGING

DEBUG = True

# Debug toolbar — disabled (incompatible with Python 3.14 in Docker)
# INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

# Relaxed security for development
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# More verbose logging in development
LOGGING = cast(dict[str, Any], _LOGGING)
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore[index]
