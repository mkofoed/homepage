import datetime
import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import structlog
from django.conf import settings
from maxminddb import Reader, open_database

logger = structlog.get_logger()


@dataclass(frozen=True)
class GeoLocation:
    ip_hash: str
    country_code: str
    country_name: str
    city: str
    latitude: float
    longitude: float


def hash_ip(ip: str) -> str:
    daily_salt = f"{settings.SECRET_KEY}:{datetime.date.today().isoformat()}"
    return hashlib.sha256(f"{daily_salt}:{ip}".encode()).hexdigest()


@lru_cache
def _get_reader() -> Reader | None:
    database_path = Path(settings.GEOIP_PATH) / "GeoLite2-City.mmdb"
    if not database_path.is_file():
        logger.warning("geoip_database_unavailable", path=str(database_path))
        return None

    return open_database(database_path)


def lookup_ip(ip: str) -> GeoLocation | None:
    """Look up an IP address using the local GeoLite2 database."""
    reader = _get_reader()
    if reader is None:
        return None

    try:
        data = reader.get(ip)
        if not isinstance(data, dict):
            return None

        record = cast(dict[str, Any], data)
        country = record.get("country", {})
        city = record.get("city", {})
        location = record.get("location", {})

        return GeoLocation(
            ip_hash=hash_ip(ip),
            country_code=country.get("iso_code", "") or "",
            country_name=country.get("names", {}).get("en", "") or "",
            city=city.get("names", {}).get("en", "") or "",
            latitude=location.get("latitude", 0.0) or 0.0,
            longitude=location.get("longitude", 0.0) or 0.0,
        )
    except TypeError, ValueError:
        logger.warning("geoip_lookup_failed", exc_info=True)
        return None
