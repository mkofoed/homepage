"""
Django development settings.
"""

import socket
from typing import Any, cast

from .base import *  # noqa: F401, F403
from .base import LOGGING as _LOGGING

DEBUG = True

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

# Internal IPs for debug toolbar (Docker-friendly)
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

# Relaxed security for development
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# More verbose logging in development
LOGGING = cast(dict[str, Any], _LOGGING)
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore[index]
