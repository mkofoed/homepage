import pendulum
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
    CPH_TZ,
    _grid_tariff_ex_vat,
    _to_cph,
)

CACHE_TIMEOUT = 60


def _total_price(spot_dkk_mwh: Decimal, ts: datetime) -> Decimal:
    """Calculate total consumer price in DKK/kWh incl. VAT from spot price in DKK/MWh.
    Pass the UTC timestamp — grid tariff is computed in Copenhagen local time internally.
    """
    spot_kwh = (spot_dkk_mwh / 1000) * DK_VAT_MULTIPLIER
    tax = (DK_ELAFGIFT + DK_ELSPAREBIDRAG) * DK_VAT_MULTIPLIER
    energinet = DK_ENERGINET_TARIFF * DK_VAT_MULTIPLIER
    grid = _grid_tariff_ex_vat(ts) * DK_VAT_MULTIPLIER
    return spot_kwh + tax + energinet + grid


@dataclass(frozen=True)
class PriceContext:
    """Everything the hero card template needs. All prices in DKK/kWh incl. VAT."""

    current_price: Decimal  # Total price (spot + all tariffs)
    spot_price: Decimal     # Spot-only component (hourly avg)
    hour_start: datetime
    day_avg: Decimal        # Used for cheap/expensive/neutral colour
    trend_pct: Decimal | None
    trend_direction: str    # "up" | "down" | "flat" | "unavailable"
    color: str              # "cheap" | "expensive" | "neutral"
    stale: bool


def _hourly_avg_spot(hour_start: datetime, price_area: str) -> Decimal | None:
    """Average spot price for all quarters in an hour. Returns DKK/MWh or None."""
    hour_end = hour_start + timedelta(hours=1)
    agg = SpotPrice.objects.filter(
        timestamp__gte=hour_start, timestamp__lt=hour_end, price_area=price_area
    ).aggregate(avg=Avg("price_dkk"))
    if agg["avg"] is not None:
        return Decimal(str(agg["avg"]))
    return None


def get_current_price(timestamp: datetime, price_area: str = "DK1") -> PriceContext | None:
    """Return current price context. All internal logic uses UTC; CPH conversion only in _grid_tariff_ex_vat."""

    cache_key = f"hero:current_price:{price_area}"
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    hour_start = timestamp.replace(minute=0, second=0, microsecond=0)
    stale = False

    avg_spot_mwh = _hourly_avg_spot(hour_start, price_area)

    if avg_spot_mwh is None:
        latest = SpotPrice.objects.filter(price_area=price_area).order_by("-timestamp").first()
        if latest is None:
            return None
        fallback_hour = latest.timestamp.replace(minute=0, second=0, microsecond=0)
        avg_spot_mwh = _hourly_avg_spot(fallback_hour, price_area)
        if avg_spot_mwh is None:
            avg_spot_mwh = latest.price_dkk
        hour_start = fallback_hour
        stale = True

    current_total = _total_price(avg_spot_mwh, hour_start)
    spot_kwh = (avg_spot_mwh / 1000) * DK_VAT_MULTIPLIER

    # Day boundary in Copenhagen time, query in UTC
    today_cph = _to_cph(timestamp).start_of("day")
    today_start = today_cph.in_timezone("UTC")
    tomorrow_start = today_cph.add(days=1).in_timezone("UTC")

    day_prices = SpotPrice.objects.filter(
        timestamp__gte=today_start, timestamp__lt=tomorrow_start, price_area=price_area
    )

    if not day_prices.exists():
        yesterday_start = today_cph.subtract(days=1).in_timezone("UTC")
        day_prices = SpotPrice.objects.filter(
            timestamp__gte=yesterday_start, timestamp__lt=today_start, price_area=price_area
        )

    if day_prices.exists():
        agg = day_prices.aggregate(avg_dkk=Avg("price_dkk"))
        # For day_avg: use average spot across the day, converted at current hour's tariff
        # This gives a reasonable "is now cheap or expensive" comparison
        day_avg = _total_price(Decimal(str(agg["avg_dkk"])), hour_start)
    else:
        day_avg = current_total

    # Trend vs same hour yesterday
    yesterday_hour_start = hour_start - timedelta(days=1)
    yesterday_avg = _hourly_avg_spot(yesterday_hour_start, price_area)

    if yesterday_avg is not None:
        yesterday_total = _total_price(yesterday_avg, yesterday_hour_start)
        if yesterday_total != 0:
            trend_pct = ((current_total - yesterday_total) / yesterday_total * 100).quantize(Decimal("0.1"))
        else:
            trend_pct = Decimal("0")
        trend_direction = (
            "up" if current_total > yesterday_total
            else "down" if current_total < yesterday_total
            else "flat"
        )
    else:
        trend_pct = None
        trend_direction = "unavailable"

    color = "cheap" if current_total < day_avg else "expensive" if current_total > day_avg else "neutral"

    price_context = PriceContext(
        current_price=current_total.quantize(Decimal("0.01")),
        spot_price=spot_kwh.quantize(Decimal("0.01")),
        hour_start=hour_start,
        day_avg=day_avg.quantize(Decimal("0.01")),
        trend_pct=trend_pct,
        trend_direction=trend_direction,
        color=color,
        stale=stale,
    )

    cache.set(cache_key, price_context, timeout=CACHE_TIMEOUT)
    return price_context
