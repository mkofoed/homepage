import sys

import django
from django.conf import settings
from django.http import HttpRequest


def site_name(request: HttpRequest) -> dict[str, str]:
    """Context processor that adds site-wide template variables."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "PYTHON_VERSION": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "DJANGO_VERSION": django.get_version(),
    }
