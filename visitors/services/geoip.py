import datetime
import hashlib
import logging

import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,lat,lon"


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
        response = httpx.get(IP_API_URL.format(ip=ip), timeout=5.0)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            logger.warning("ip-api.com lookup failed for IP: %s", data.get("message", "unknown"))
            return None

        return GeoLocation(
            ip_hash=hash_ip(ip),
            country_code=data.get("countryCode", "") or "",
            country_name=data.get("country", "") or "",
            city=data.get("city", "") or "",
            latitude=data.get("lat", 0.0) or 0.0,
            longitude=data.get("lon", 0.0) or 0.0,
        )
    except Exception:
        logger.warning("ip-api.com lookup failed", exc_info=True)
        return None
