import json
from dataclasses import asdict

from django.shortcuts import render
from django.utils import timezone

from dashboard.services.price_chart import get_chart_data


def dashboard_home(request):
    """
    Renders the main dashboard skeleton containing the empty chart canvas.
    HTMX will immediately replace the canvas contents on load.
    """
    return render(request, "dashboard/index.html")


def htmx_price_chart(request):
    """
    HTMX endpoint: returns chart data for the requested time range.
    All business logic lives in dashboard.services.price_chart.
    """
    range_param = request.GET.get("range", "default")
    now = timezone.now()
    chart_data = get_chart_data(range_param=range_param, now=now)

    # Find the current 15-minute interval to highlight "price right now"
    minute_bucket = (now.minute // 15) * 15
    current_interval = now.replace(minute=minute_bucket, second=0, microsecond=0)

    context = {
        "chart_data_json": json.dumps(asdict(chart_data)),
        "current_interval_iso": current_interval.isoformat(),
        "active_range": range_param,
    }

    return render(request, "dashboard/partials/chart_data.html", context)
