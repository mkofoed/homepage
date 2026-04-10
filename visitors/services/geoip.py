import datetime
import hashlib
import logging
from dataclasses import dataclass

from django.contrib.gis.geoip2 import GeoIP2

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeoLocation:
    ip_hash: str
    country_code: str
    country_name: str
    city: str
    latitude: float
    longitude: float


def hash_ip(ip: str) -> str:
    daily_salt = f"mkofoed-{datetime.date.today().isoformat()}"
    return hashlib.sha256(f"{daily_salt}:{ip}".encode()).hexdigest()


def lookup_ip(ip: str) -> GeoLocation | None:
    try:
        g = GeoIP2()
        data = g.city(ip)
        return GeoLocation(
            ip_hash=hash_ip(ip),
            country_code=data.get("country_code", "") or "",
            country_name=data.get("country_name", "") or "",
            city=data.get("city", "") or "",
            latitude=round(data.get("latitude", 0.0) or 0.0, 2),
            longitude=round(data.get("longitude", 0.0) or 0.0, 2),
        )
    except Exception:
        logger.warning("GeoIP lookup failed for IP", exc_info=True)
        return None
