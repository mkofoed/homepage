import json
from django.shortcuts import render
from dashboard.models import SpotPrice


def dashboard_home(request):
    """
    Renders the main dashboard skeleton containing the empty chart canvas.
    HTMX will immediately replace the canvas contents on load.
    """
    return render(request, "dashboard/index.html")


def htmx_price_chart(request):
    """
    HTMX endpoint that queries the latest 24 hours of spot prices, formats
    the labels and data for Chart.js, and returns it inside a script tag
    to re-render the chart.
    """
    from django.utils import timezone
    from django.db.models import Avg
    from django.db.models.functions import TruncHour, TruncDay
    from datetime import timedelta

    range_param = request.GET.get("range", "default")
    now = timezone.now()

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
        # Fallback to week
        range_param = "week"
        start_time = now - timedelta(days=7)
        qs = SpotPrice.objects.filter(timestamp__gte=start_time).order_by("timestamp")

    labels = []
    data_spot = []
    data_tax = []
    data_system = []
    data_grid = []
    data_vat = []

    for item in qs:
        # Extract timestamp and base spot price
        if range_param in ["month", "year"]:
            ts = item["period"]
            spot_dkk_mwh = item["avg_price_dkk"]
        else:
            ts = item.timestamp
            spot_dkk_mwh = float(item.price_dkk)

        spot_kwh = (float(spot_dkk_mwh) / 1000.0) * 1.25

        tax = 0.008 * 1.25  # 2026 Danish Electricity Tax Rate
        system_tariff = 0.136 * 1.25 # Current Energinet System Tariff 
        
        # Grid Tariff logic (Estimate based on standard DK1 Operator e.g. TREFOR / Radius)
        month = ts.month
        hour = ts.hour
        is_winter = month in [10, 11, 12, 1, 2, 3]
        
        if range_param == "year":
            # Rough daily average for grid tariff
            grid_tariff = (0.34 if is_winter else 0.16) * 1.25
        else:
            if 17 <= hour < 21:
                # Peak
                grid_tariff = (0.70 if is_winter else 0.25) * 1.25
            elif (6 <= hour < 17) or (21 <= hour < 24):
                # High Load (kl. 23)
                grid_tariff = (0.24 if is_winter else 0.15) * 1.25
            else:
                # Low Load (00 - 06)
                grid_tariff = 0.10 * 1.25

        labels.append(ts.isoformat())
        data_spot.append(round(spot_kwh, 2))
        data_tax.append(round(tax, 2))
        data_system.append(round(system_tariff, 2))
        data_grid.append(round(grid_tariff, 2))

    chart_data = {
        "labels": labels,
        "data_spot": data_spot,
        "data_tax": data_tax,
        "data_system": data_system,
        "data_grid": data_grid,
    }

    # Find the current 15-minute interval to highlight the "price right now"
    minute_bucket = (now.minute // 15) * 15
    current_interval = now.replace(minute=minute_bucket, second=0, microsecond=0)

    context = {
        "chart_data_json": json.dumps(chart_data),
        "current_interval_iso": current_interval.isoformat(),
        "active_range": range_param,
    }

    return render(request, "dashboard/partials/chart_data.html", context)
