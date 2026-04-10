import json

from django.shortcuts import render
from dashboard.services.price_chart import get_chart_data

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
    range_param = request.GET.get("range", "default")
    chart_data = get_chart_data(range_param=range_param, now=timezone.now())

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



    # Find the current 15-minute interval to highlight the "price right now"
    minute_bucket = (now.minute // 15) * 15
    current_interval = now.replace(minute=minute_bucket, second=0, microsecond=0)

    context = {
        "chart_data_json": json.dumps(chart_data),
        "current_interval_iso": current_interval.isoformat(),
        "active_range": range_param,
    }

    return render(request, "dashboard/partials/chart_data.html", context)
