from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Avg, Max, Min

from dashboard.models import SpotPrice
from dashboard.services.price_chart import (
    DK_ELAFGIFT,
    DK_ELSPAREBIDRAG,
    DK_ENERGINET_TARIFF,
    DK_VAT_MULTIPLIER,
    _grid_tariff_ex_vat,
)

CACHE_TIMEOUT = 60


def _total_price(spot_dkk_mwh: Decimal, hour: int, month: int) -> Decimal:
    """Calculate total consumer price in DKK/kWh incl. VAT from spot price in DKK/MWh."""
    spot_kwh = (spot_dkk_mwh / 1000) * DK_VAT_MULTIPLIER
    tax = (DK_ELAFGIFT + DK_ELSPAREBIDRAG) * DK_VAT_MULTIPLIER
    energinet = DK_ENERGINET_TARIFF * DK_VAT_MULTIPLIER
    grid = _grid_tariff_ex_vat(hour, month) * DK_VAT_MULTIPLIER
    return spot_kwh + tax + energinet + grid


@dataclass(frozen=True)
class PriceContext:
    """Everything the hero card template needs. All prices in DKK/kWh incl. VAT."""

    current_price: Decimal  # Total price (spot + all tariffs)
    spot_price: Decimal  # Spot-only component (hourly avg)
    hour_start: datetime
    day_min: Decimal
    day_max: Decimal
    day_avg: Decimal
    trend_pct: Decimal | None
    trend_direction: str  # "up" | "down" | "flat" | "unavailable"
    color: str  # "cheap" | "expensive" | "neutral"
    stale: bool


def _hourly_avg_spot(hour_start: datetime, price_area: str) -> Decimal | None:
    """Average spot price for all quarters in an hour. Returns DKK/MWh or None."""
    hour_end = hour_start + timedelta(hours=1)
    agg = SpotPrice.objects.filter(timestamp__gte=hour_start, timestamp__lt=hour_end, price_area=price_area).aggregate(
        avg=Avg("price_dkk")
    )
    if agg["avg"] is not None:
        return Decimal(str(agg["avg"]))
    return None


def get_current_price(timestamp: datetime, price_area: str = "DK1") -> PriceContext | None:
    """Return current price context. Averages all quarters in the current hour."""

    cache_key = f"hero:current_price:{price_area}"
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    hour_start = timestamp.replace(minute=0, second=0, microsecond=0)
    stale = False

    # Average all quarters in current hour (matches chart hourly view)
    avg_spot_mwh = _hourly_avg_spot(hour_start, price_area)

    if avg_spot_mwh is None:
        # Try most recent hour with data
        latest = SpotPrice.objects.filter(price_area=price_area).order_by("-timestamp").first()
        if latest is None:
            return None
        fallback_hour = latest.timestamp.replace(minute=0, second=0, microsecond=0)
        avg_spot_mwh = _hourly_avg_spot(fallback_hour, price_area)
        if avg_spot_mwh is None:
            avg_spot_mwh = latest.price_dkk
        hour_start = fallback_hour
        stale = True

    current_total = _total_price(avg_spot_mwh, timestamp.hour, timestamp.month)
    spot_kwh = (avg_spot_mwh / 1000) * DK_VAT_MULTIPLIER

    # Daily aggregates — also use hourly averages for consistency
    today_start = hour_start.replace(hour=0)
    tomorrow_start = today_start + timedelta(days=1)
    day_prices = SpotPrice.objects.filter(
        timestamp__gte=today_start, timestamp__lt=tomorrow_start, price_area=price_area
    )

    if not day_prices.exists():
        yesterday_start = today_start - timedelta(days=1)
        day_prices = SpotPrice.objects.filter(
            timestamp__gte=yesterday_start, timestamp__lt=today_start, price_area=price_area
        )

    if day_prices.exists():
        agg = day_prices.aggregate(
            day_min=Min("price_dkk"),
            day_max=Max("price_dkk"),
            day_avg=Avg("price_dkk"),
        )
        day_min = _total_price(agg["day_min"], 3, timestamp.month)
        day_max = _total_price(agg["day_max"], 18, timestamp.month)
        day_avg = _total_price(Decimal(str(agg["day_avg"])), 12, timestamp.month)
    else:
        day_min = day_max = day_avg = current_total

    # Trend vs same hour yesterday (also averaged)
    yesterday_hour_start = hour_start - timedelta(days=1)
    yesterday_avg = _hourly_avg_spot(yesterday_hour_start, price_area)

    if yesterday_avg is not None:
        yesterday_total = _total_price(
            yesterday_avg,
            yesterday_hour_start.hour,
            yesterday_hour_start.month,
        )
        if yesterday_total != 0:
            trend_pct = ((current_total - yesterday_total) / yesterday_total * 100).quantize(Decimal("0.1"))
        else:
            trend_pct = Decimal("0")
        trend_direction = (
            "up" if current_total > yesterday_total else "down" if current_total < yesterday_total else "flat"
        )
    else:
        trend_pct = None
        trend_direction = "unavailable"

    color = "cheap" if current_total < day_avg else "expensive" if current_total > day_avg else "neutral"

    price_context = PriceContext(
        current_price=current_total.quantize(Decimal("0.01")),
        spot_price=spot_kwh.quantize(Decimal("0.01")),
        hour_start=hour_start,
        day_min=day_min.quantize(Decimal("0.01")),
        day_max=day_max.quantize(Decimal("0.01")),
        day_avg=day_avg.quantize(Decimal("0.01")),
        trend_pct=trend_pct,
        trend_direction=trend_direction,
        color=color,
        stale=stale,
    )

    cache.set(cache_key, price_context, timeout=CACHE_TIMEOUT)
    return price_context
