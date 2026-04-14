import pendulum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.core.cache import cache
from django.db.models import Avg, QuerySet
from django.db.models.functions import TruncDay, TruncHour

from dashboard.models import SpotPrice

# 2026 Danish electricity tariffs (ex VAT)
# Sources: energinet.dk, eloversigt.dk, skat.dk (L24)
DK_VAT_MULTIPLIER = Decimal("1.25")
DK_ELAFGIFT = Decimal("0.008")        # Elafgift 2026-2027: 0.8 øre/kWh
DK_ELSPAREBIDRAG = Decimal("0.006")   # Elsparebidrag: 0.6 øre/kWh
DK_ENERGINET_TARIFF = Decimal("0.092")  # Energinet system+transmission 2026: 9.2 øre/kWh

# N1 grid tariffs 2026 (ex VAT) — covers Aarhus/most of Jylland
N1_GRID_TARIFFS = {
    "winter": {"peak": Decimal("0.3426"), "day": Decimal("0.1318"), "night": Decimal("0.0879")},
    "summer": {"peak": Decimal("0.1218"), "day": Decimal("0.0468"), "night": Decimal("0.0312")},
}

# Backward compatibility aliases
DK_ELECTRICITY_TAX_2026 = DK_ELAFGIFT
DK_ENERGINET_SYSTEM_TARIFF = DK_ENERGINET_TARIFF

CPH_TZ = pendulum.timezone("Europe/Copenhagen")


def _to_cph(ts: datetime) -> pendulum.DateTime:
    """Convert any aware datetime to a Copenhagen pendulum DateTime."""
    return pendulum.instance(ts).in_timezone(CPH_TZ)


def _grid_tariff_ex_vat(ts: datetime) -> Decimal:
    """N1 grid tariff based on Copenhagen local time-of-use (ex VAT).
    Always pass UTC-aware timestamps — timezone conversion is handled internally.
    """
    t = _to_cph(ts)
    season = "winter" if t.month in [10, 11, 12, 1, 2, 3] else "summer"
    if 17 <= t.hour < 21:
        period = "peak"
    elif (6 <= t.hour < 17) or (21 <= t.hour < 24):
        period = "day"
    else:
        period = "night"
    return N1_GRID_TARIFFS[season][period]


def _period_bounds(range_param: str, now: datetime, offset: int = 0) -> tuple[datetime, datetime, str]:
    """
    Return (start_utc, end_utc, period_label) for the given range and offset.
    Day: calendar day in Copenhagen time.
    Week/month/year: rolling windows (last 7/30/365 days) with offset support.
    All returned datetimes are UTC-aware pendulum DateTimes.
    """
    now_cph = _to_cph(now)

    if range_param in ["day", "default"]:
        start = now_cph.start_of("day").add(days=offset)
        end = start.add(days=1)
        label = start.format("D. MMM YYYY", locale="da")

    elif range_param == "week":
        # Rolling 7-day window
        end = now_cph.start_of("day").add(days=1 + offset * 7)  # end of target window
        start = end.subtract(days=7)
        label = f"{start.format('D. MMM', locale='da')} \u2013 {end.subtract(days=1).format('D. MMM', locale='da')}"

    elif range_param == "month":
        # Rolling 30-day window
        end = now_cph.start_of("day").add(days=1 + offset * 30)
        start = end.subtract(days=30)
        label = f"{start.format('D. MMM', locale='da')} \u2013 {end.subtract(days=1).format('D. MMM', locale='da')}"

    elif range_param == "year":
        # Rolling 365-day window
        end = now_cph.start_of("day").add(days=1 + offset * 365)
        start = end.subtract(days=365)
        label = f"{start.format('D. MMM YYYY', locale='da')} \u2013 {end.subtract(days=1).format('D. MMM YYYY', locale='da')}"

    else:
        return _period_bounds("week", now, offset)

    return start.in_timezone("UTC"), end.in_timezone("UTC"), label


@dataclass
class ChartData:
    """Two-component chart data matching Danish energy provider presentation."""

    labels: list[str]
    data_elpris: list[float]
    data_transport: list[float]
    data_total: list[float]
    period_label: str  # e.g. "10. apr 2026", "Uge 15 (7/4 – 13/4)"


def get_chart_data(
    range_param: str, now: datetime, resolution: str = "quarter", offset: int = 0, price_area: str = "DK1"
) -> ChartData:
    cache_key = f"price_chart:{range_param}:{resolution}:{offset}:{price_area}"
    cached_data: ChartData | None = cache.get(cache_key)
    if cached_data:
        return cached_data

    start_time, end_time, period_label = _period_bounds(range_param, now, offset)

    base_qs = SpotPrice.objects.filter(timestamp__gte=start_time, timestamp__lt=end_time, price_area=price_area)

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
    elif range_param == "month" or resolution in ("hour", "day"):
        trunc = TruncDay("timestamp") if resolution == "day" else TruncHour("timestamp")
        qs = (
            base_qs.annotate(period=trunc)
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
        elpris = spot_kwh + tax_incl

        if range_param == "year":
            # For year view use an average grid tariff (daily resolution, tariff detail not meaningful)
            t = _to_cph(ts)
            season = "winter" if t.month in [10, 11, 12, 1, 2, 3] else "summer"
            tariffs = N1_GRID_TARIFFS[season]
            avg_grid = float(
                (tariffs["night"] * 6 + tariffs["day"] * 14 + tariffs["peak"] * 4) / 24 * DK_VAT_MULTIPLIER
            )
            transport = energinet_incl + avg_grid
        else:
            grid_incl = float(_grid_tariff_ex_vat(ts) * DK_VAT_MULTIPLIER)
            transport = energinet_incl + grid_incl

        total = elpris + transport

        # Label is Copenhagen local time — chart.js renders as-is, no TZ conversion needed
        labels.append(_to_cph(ts).format("YYYY-MM-DDTHH:mm:ss"))
        data_elpris.append(round(elpris, 4))
        data_transport.append(round(transport, 4))
        data_total.append(round(total, 4))

    # For day view: pad to full skeleton so x-axis always covers 00-23
    # Missing slots show as null (Chart.js leaves gaps visually)
    if range_param in ("day", "default"):
        day_start = _to_cph(start_time)
        if resolution == "quarter":
            # 96 slots at 15-min intervals
            full_labels = [day_start.add(minutes=m*15).format("YYYY-MM-DDTHH:mm:ss") for m in range(96)]
        else:
            # 24 hourly slots
            full_labels = [day_start.add(hours=h).format("YYYY-MM-DDTHH:mm:ss") for h in range(24)]
        existing = {l: (e, tr, tot) for l, e, tr, tot in zip(labels, data_elpris, data_transport, data_total)}
        labels = full_labels
        data_elpris = [existing.get(l, (None,))[0] for l in full_labels]  # type: ignore
        data_transport = [existing.get(l, (None, None))[1] for l in full_labels]  # type: ignore
        data_total = [existing.get(l, (None, None, None))[2] for l in full_labels]  # type: ignore

    chart_data = ChartData(
        labels=labels,
        data_elpris=data_elpris,
        data_transport=data_transport,
        data_total=data_total,
        period_label=period_label,
    )

    cache_ttl = 60 if range_param == "day" else 600  # longer ranges change slowly
    cache.set(cache_key, chart_data, timeout=cache_ttl)
    return chart_data
