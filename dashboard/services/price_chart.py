from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Avg
from django.db.models.functions import TruncDay, TruncHour

from dashboard.models import SpotPrice

DK_ELECTRICITY_TAX_2026 = Decimal("0.008")
DK_VAT_MULTIPLIER = Decimal("1.25")
DK_ENERGINET_SYSTEM_TARIFF = Decimal("0.136")


@dataclass
class ChartData:
    labels: list[str]
    data_spot: list[float]
    data_tax: list[float]
    data_system: list[float]
    data_grid: list[float]


def get_chart_data(range_param: str, now: datetime) -> ChartData:
    if range_param in ["day", "default"]:
        start_time = now - timedelta(days=1)
        qs = SpotPrice.objects.filter(timestamp__gte=start_time).order_by("timestamp")
    elif range_param == "week":
        start_time = now - timedelta(days=7)
        qs = SpotPrice.objects.filter(timestamp__gte=start_time).order_by("timestamp")
    elif range_param == "month":
        start_time = now - timedelta(days=30)
        qs = (
            SpotPrice.objects.filter(timestamp__gte=start_time)
            .annotate(period=TruncHour("timestamp"))
            .values("period")
            .annotate(avg_price_dkk=Avg("price_dkk"))
            .order_by("period")
        )
    elif range_param == "year":
        start_time = now - timedelta(days=365)
        qs = (
            SpotPrice.objects.filter(timestamp__gte=start_time)
            .annotate(period=TruncDay("timestamp"))
            .values("period")
            .annotate(avg_price_dkk=Avg("price_dkk"))
            .order_by("period")
        )
    else:
        range_param = "week"
        start_time = now - timedelta(days=7)
        qs = SpotPrice.objects.filter(timestamp__gte=start_time).order_by("timestamp")

    labels, data_spot, data_tax, data_system, data_grid = [], [], [], [], []

    for item in qs:
        if range_param in ["month", "year"]:
            ts = item["period"]
            spot_dkk_mwh = item["avg_price_dkk"]
        else:
            ts = item.timestamp
            spot_dkk_mwh = float(item.price_dkk)

        spot_kwh = (Decimal(spot_dkk_mwh) / 1000) * DK_VAT_MULTIPLIER
        tax = DK_ELECTRICITY_TAX_2026 * DK_VAT_MULTIPLIER
        system_tariff = DK_ENERGINET_SYSTEM_TARIFF * DK_VAT_MULTIPLIER

        month = ts.month
        hour = ts.hour
        is_winter = month in [10, 11, 12, 1, 2, 3]

        if range_param == "year":
            grid_tariff = (0.34 if is_winter else 0.16) * DK_VAT_MULTIPLIER
        else:
            if 17 <= hour < 21:
                grid_tariff = (0.70 if is_winter else 0.25) * DK_VAT_MULTIPLIER
            elif (6 <= hour < 17) or (21 <= hour < 24):
                grid_tariff = (0.24 if is_winter else 0.15) * DK_VAT_MULTIPLIER
            else:
                grid_tariff = 0.10 * DK_VAT_MULTIPLIER

        labels.append(ts.isoformat())
        data_spot.append(round(float(spot_kwh), 2))
        data_tax.append(round(float(tax), 2))
        data_system.append(round(float(system_tariff), 2))
        data_grid.append(round(float(grid_tariff), 2))

    return ChartData(
        labels=labels, data_spot=data_spot, data_tax=data_tax, data_system=data_system, data_grid=data_grid
    )
