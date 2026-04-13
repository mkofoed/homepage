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

    import zoneinfo
    CPH_TZ = zoneinfo.ZoneInfo("Europe/Copenhagen")
    minute_bucket = (now.minute // 15) * 15
    current_interval = now.replace(minute=minute_bucket, second=0, microsecond=0)
    current_interval_cph = current_interval.astimezone(CPH_TZ).strftime("%Y-%m-%dT%H:%M:%S")

    # Compute summary stats
    # For day view: use chart data directly (already 15min or hourly resolution)
    # For week/month/year: query actual DB min/max since chart data uses averages
    summary = {}
    if chart_data.data_total:
        def _time_label(iso_str: str, res: str, rng: str, exact: bool = False) -> str:
            """Format time label in Copenhagen time, resolution and range aware.
            If exact=True, always include the hour (used for actual min/max records)."""
            da_days = ['man', 'tir', 'ons', 'tor', 'fre', 'l\u00f8r', 's\u00f8n']
            da_months = ['', 'jan', 'feb', 'mar', 'apr', 'maj', 'jun',
                         'jul', 'aug', 'sep', 'okt', 'nov', 'dec']
            try:
                t = dt.fromisoformat(iso_str)
                t_cph = t.astimezone(CPH_TZ)
                wd = da_days[t_cph.weekday()]
                mo = da_months[t_cph.month]
                if exact:
                    # Always show full date + hour for actual extreme records
                    return f"{wd} {t_cph.day}. {mo} kl. {t_cph.hour:02d}-{(t_cph.hour + 1) % 24:02d}"
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

        if range_param in ('week', 'month', 'year'):
            from dashboard.models import SpotPrice
            from django.db.models import Min, Max
            from dashboard.services.price_chart import _period_bounds, DK_VAT_MULTIPLIER, DK_ELAFGIFT, DK_ELSPAREBIDRAG, DK_ENERGINET_TARIFF, _grid_tariff_ex_vat
            from decimal import Decimal as _D

            start_time, end_time, _ = _period_bounds(range_param, now, offset)
            agg = SpotPrice.objects.filter(
                timestamp__gte=start_time, timestamp__lt=end_time, price_area=price_area
            ).aggregate(min_dkk=Min('price_dkk'), max_dkk=Max('price_dkk'))

            min_record = SpotPrice.objects.filter(
                timestamp__gte=start_time, timestamp__lt=end_time,
                price_area=price_area, price_dkk=agg['min_dkk']
            ).first()
            max_record = SpotPrice.objects.filter(
                timestamp__gte=start_time, timestamp__lt=end_time,
                price_area=price_area, price_dkk=agg['max_dkk']
            ).first()

            def _spot_to_total(spot_dkk_mwh, hour, month):
                spot_kwh = float((_D(str(float(spot_dkk_mwh))) / 1000) * DK_VAT_MULTIPLIER)
                tax = float((DK_ELAFGIFT + DK_ELSPAREBIDRAG) * DK_VAT_MULTIPLIER)
                energinet = float(DK_ENERGINET_TARIFF * DK_VAT_MULTIPLIER)
                grid = float(_grid_tariff_ex_vat(hour, month) * DK_VAT_MULTIPLIER)
                return spot_kwh + tax + energinet + grid

            min_ts = min_record.timestamp.astimezone(CPH_TZ).isoformat() if min_record else chart_data.labels[0]
            max_ts = max_record.timestamp.astimezone(CPH_TZ).isoformat() if max_record else chart_data.labels[0]
            min_h = min_record.timestamp.astimezone(CPH_TZ).hour if min_record else 0
            max_h = max_record.timestamp.astimezone(CPH_TZ).hour if max_record else 0
            min_mo = min_record.timestamp.astimezone(CPH_TZ).month if min_record else now.month
            max_mo = max_record.timestamp.astimezone(CPH_TZ).month if max_record else now.month

            min_val = _spot_to_total(agg['min_dkk'], min_h, min_mo)
            max_val = _spot_to_total(agg['max_dkk'], max_h, max_mo)
            avg_val = sum(chart_data.data_total) / len(chart_data.data_total)

            summary = {
                "min_price": f"{min_val:.2f}",
                "min_hour": _time_label(min_ts, resolution, range_param, exact=True),
                "max_price": f"{max_val:.2f}",
                "max_hour": _time_label(max_ts, resolution, range_param, exact=True),
                "avg_price": f"{avg_val:.2f}",
            }
        else:
            min_val = min(chart_data.data_total)
            max_val = max(chart_data.data_total)
            avg_val = sum(chart_data.data_total) / len(chart_data.data_total)
            min_idx = chart_data.data_total.index(min_val)
            max_idx = chart_data.data_total.index(max_val)
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
        "current_interval_iso": current_interval_cph,
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
