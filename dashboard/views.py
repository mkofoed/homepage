import json
import zoneinfo
from dataclasses import asdict
from datetime import datetime as dt

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from dashboard.services.current_price import get_current_price
from dashboard.services.price_chart import get_chart_data

CPH_TZ = zoneinfo.ZoneInfo("Europe/Copenhagen")


def dashboard_home(request: HttpRequest) -> HttpResponse:
    """Renders the main dashboard skeleton. HTMX loads the dynamic parts."""
    return render(request, "dashboard/index.html", {"active_area": "DK1"})


def htmx_price_chart(request: HttpRequest) -> HttpResponse:
    """HTMX endpoint: returns chart data for the requested time range, resolution and offset."""
    range_param = request.GET.get("range", "day")
    resolution = request.GET.get("resolution", "hour")
    offset = int(request.GET.get("offset", "0"))

    if range_param == "default":
        range_param = "day"
    if resolution not in ("quarter", "hour"):
        resolution = "hour"

    now = timezone.now()
    price_area = request.GET.get("area", "DK1")
    if price_area not in ["DK1", "DK2"]:
        price_area = "DK1"
    chart_data = get_chart_data(
        range_param=range_param, now=now, resolution=resolution, offset=offset, price_area=price_area
    )

    minute_bucket = (now.minute // 15) * 15
    current_interval = now.replace(minute=minute_bucket, second=0, microsecond=0)

    # Compute summary stats from the total data
    summary = {}
    if chart_data.data_total:
        min_val = min(chart_data.data_total)
        max_val = max(chart_data.data_total)
        avg_val = sum(chart_data.data_total) / len(chart_data.data_total)

        min_idx = chart_data.data_total.index(min_val)
        max_idx = chart_data.data_total.index(max_val)

        def _time_label(iso_str: str, res: str, rng: str) -> str:
            """Format time label in Copenhagen time, resolution and range aware."""
            da_days = ['man', 'tir', 'ons', 'tor', 'fre', 'lør', 'søn']
            da_months = ['', 'jan', 'feb', 'mar', 'apr', 'maj', 'jun',
                         'jul', 'aug', 'sep', 'okt', 'nov', 'dec']
            try:
                t = dt.fromisoformat(iso_str)
                t_cph = t.astimezone(CPH_TZ)
                wd = da_days[t_cph.weekday()]
                mo = da_months[t_cph.month]
                if rng == "year":
                    return mo.capitalize()
                if rng == "month":
                    return f"{wd} {t_cph.day}. {mo}"
                if rng == "week":
                    return f"{wd} {t_cph.day}/{t_cph.month} kl. {t_cph.hour:02d}"
                if res == "quarter":
                    from datetime import timedelta as _td
                    end = t_cph + _td(minutes=15)
                    return f"Kl. {t_cph.hour:02d}:{t_cph.minute:02d}-{end.hour:02d}:{end.minute:02d}"
                return f"Kl. {t_cph.hour:02d}-{(t_cph.hour + 1) % 24:02d}"
            except (ValueError, AttributeError):
                return ""

        summary = {
            "min_price": f"{min_val:.2f}",
            "min_hour": _time_label(chart_data.labels[min_idx], resolution, range_param),
            "max_price": f"{max_val:.2f}",
            "max_hour": _time_label(chart_data.labels[max_idx], resolution, range_param),
            "avg_price": f"{avg_val:.2f}",
        }

    # Serialize chart data but exclude period_label from JSON (passed separately)
    chart_dict = asdict(chart_data)
    period_label = chart_dict.pop("period_label", "")

    context = {
        "chart_data_json": json.dumps(chart_dict),
        "current_interval_iso": current_interval.isoformat(),
        "active_range": range_param,
        "summary_json": json.dumps(summary),
        "active_area": price_area,
        "period_label": period_label,
        "offset": offset,
    }
    return render(request, "dashboard/partials/chart_data.html", context)


def htmx_hero_card(request: HttpRequest) -> HttpResponse:
    """HTMX endpoint: returns the current price hero card partial."""
    now = timezone.now()
    price_area = request.GET.get("area", "DK1")
    if price_area not in ["DK1", "DK2"]:
        price_area = "DK1"
    ctx = get_current_price(now, price_area=price_area)
    if ctx is None:
        return render(request, "dashboard/partials/hero_card.html", {"unavailable": True})
    return render(request, "dashboard/partials/hero_card.html", {"price": ctx, "unavailable": False})
