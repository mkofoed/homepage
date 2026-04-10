import zoneinfo
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.core.cache import cache
from django.db.models import Avg, QuerySet
from django.db.models.functions import TruncDay, TruncHour

from dashboard.models import SpotPrice

# 2026 Danish electricity tariffs (ex VAT)
# Sources: energinet.dk, eloversigt.dk, skat.dk (L24)
DK_VAT_MULTIPLIER = Decimal("1.25")
DK_ELAFGIFT = Decimal("0.008")  # Elafgift 2026-2027: 0.8 øre/kWh (reduced to EU min by L24)
DK_ELSPAREBIDRAG = Decimal("0.006")  # Elsparebidrag: 0.6 øre/kWh
DK_ENERGINET_TARIFF = Decimal("0.092")  # Energinet system+transmission 2026: 9.2 øre/kWh

# N1 grid tariffs 2026 (ex VAT) — covers Aarhus/most of Jylland
N1_GRID_TARIFFS = {
    "winter": {"peak": Decimal("0.3426"), "day": Decimal("0.1318"), "night": Decimal("0.0879")},
    "summer": {"peak": Decimal("0.1218"), "day": Decimal("0.0468"), "night": Decimal("0.0312")},
}

# Backward compatibility aliases
DK_ELECTRICITY_TAX_2026 = DK_ELAFGIFT
DK_ENERGINET_SYSTEM_TARIFF = DK_ENERGINET_TARIFF

CPH_TZ = zoneinfo.ZoneInfo("Europe/Copenhagen")


def _grid_tariff_ex_vat(hour: int, month: int) -> Decimal:
    """N1 grid tariff based on time-of-use (ex VAT)."""
    season = "winter" if month in [10, 11, 12, 1, 2, 3] else "summer"
    if 17 <= hour < 21:
        period = "peak"
    elif (6 <= hour < 17) or (21 <= hour < 24):
        period = "day"
    else:
        period = "night"
    return N1_GRID_TARIFFS[season][period]


def _period_bounds(
    range_param: str, now: datetime, offset: int = 0
) -> tuple[datetime, datetime, str]:
    """
    Return (start_utc, end_utc, period_label) for the given range and offset.
    offset=0 is current period, -1 is previous, +1 is next.
    All boundaries are in Copenhagen time, converted to UTC for querying.
    """
    now_cph = now.astimezone(CPH_TZ)

    if range_param in ["day", "default"]:
        base = now_cph.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=offset)
        start_cph = base
        end_cph = base + timedelta(days=1)
        # For today (offset=0), include tomorrow's day-ahead prices
        if offset == 0:
            end_cph = base + timedelta(days=2)
        label = base.strftime("%-d. %b %Y")

    elif range_param == "week":
        # Monday of current week
        today = now_cph.replace(hour=0, minute=0, second=0, microsecond=0)
        monday = today - timedelta(days=today.weekday())
        monday = monday + timedelta(weeks=offset)
        start_cph = monday
        end_cph = monday + timedelta(weeks=1)
        end_of_week = end_cph - timedelta(days=1)
        label = f"Uge {monday.isocalendar()[1]} ({monday.strftime('%-d/%-m')} – {end_of_week.strftime('%-d/%-m')})"

    elif range_param == "month":
        # First of current month
        first = now_cph.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Apply offset
        month = first.month + offset
        year = first.year
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        start_cph = first.replace(year=year, month=month, day=1)
        # End = first of next month
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        end_cph = first.replace(year=next_year, month=next_month, day=1)
        label = start_cph.strftime("%B %Y")

    elif range_param == "year":
        year = now_cph.year + offset
        start_cph = now_cph.replace(year=year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_cph = start_cph.replace(year=year + 1)
        label = str(year)

    else:
        # Fallback to week
        return _period_bounds("week", now, offset)

    # Convert to UTC
    start_utc = start_cph.astimezone(now.tzinfo) if now.tzinfo else start_cph
    end_utc = end_cph.astimezone(now.tzinfo) if now.tzinfo else end_cph

    return start_utc, end_utc, label


@dataclass
class ChartData:
    """Two-component chart data matching Danish energy provider presentation."""

    labels: list[str]
    data_elpris: list[float]
    data_transport: list[float]
    data_total: list[float]
    period_label: str  # e.g. "10. apr 2026", "Uge 15 (7/4 – 13/4)"


def get_chart_data(
    range_param: str, now: datetime, resolution: str = "quarter", offset: int = 0
) -> ChartData:
    cache_key = f"price_chart:{range_param}:{resolution}:{offset}"
    cached_data: ChartData | None = cache.get(cache_key)
    if cached_data:
        return cached_data

    start_time, end_time, period_label = _period_bounds(range_param, now, offset)

    base_qs = SpotPrice.objects.filter(timestamp__gte=start_time, timestamp__lt=end_time)

    qs: QuerySet[Any]
    aggregate_field: str | None = None

    if range_param == "year":
        qs = (
            base_qs.annotate(period=TruncDay("timestamp"))
            .values("period")
            .annotate(avg_price_dkk=Avg("price_dkk"))
            .order_by("period")
        )
        aggregate_field = "avg_price_dkk"
    elif range_param == "month" or resolution == "hour":
        qs = (
            base_qs.annotate(period=TruncHour("timestamp"))
            .values("period")
            .annotate(avg_price_dkk=Avg("price_dkk"))
            .order_by("period")
        )
        aggregate_field = "avg_price_dkk"
    else:
        qs = base_qs.order_by("timestamp")
        aggregate_field = None

    labels: list[str] = []
    data_elpris: list[float] = []
    data_transport: list[float] = []
    data_total: list[float] = []

    tax_incl = float((DK_ELAFGIFT + DK_ELSPAREBIDRAG) * DK_VAT_MULTIPLIER)
    energinet_incl = float(DK_ENERGINET_TARIFF * DK_VAT_MULTIPLIER)

    for item in qs:
        if aggregate_field is not None:
            row: dict[str, Any] = item  # type: ignore[assignment]
            ts: datetime = row["period"]
            spot_dkk_mwh = float(row[aggregate_field])
        else:
            record: SpotPrice = item  # type: ignore[assignment]
            ts = record.timestamp
            spot_dkk_mwh = float(record.price_dkk)

        spot_kwh = float((Decimal(str(spot_dkk_mwh)) / 1000) * DK_VAT_MULTIPLIER)
        month = ts.month
        hour = ts.hour

        elpris = spot_kwh + tax_incl

        if range_param == "year":
            season = "winter" if month in [10, 11, 12, 1, 2, 3] else "summer"
            tariffs = N1_GRID_TARIFFS[season]
            avg_grid = float(
                (tariffs["night"] * 6 + tariffs["day"] * 14 + tariffs["peak"] * 4)
                / 24
                * DK_VAT_MULTIPLIER
            )
            transport = energinet_incl + avg_grid
        else:
            grid_incl = float(_grid_tariff_ex_vat(hour, month) * DK_VAT_MULTIPLIER)
            transport = energinet_incl + grid_incl

        total = elpris + transport

        labels.append(ts.isoformat())
        data_elpris.append(round(elpris, 4))
        data_transport.append(round(transport, 4))
        data_total.append(round(total, 4))

    chart_data = ChartData(
        labels=labels,
        data_elpris=data_elpris,
        data_transport=data_transport,
        data_total=data_total,
        period_label=period_label,
    )

    cache.set(cache_key, chart_data, timeout=300)
    return chart_data
