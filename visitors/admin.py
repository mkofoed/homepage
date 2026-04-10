from django.contrib import admin
from .models import PageView

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "city", "country_code", "path", "device_type")
    list_filter = ("country_code", "device_type")
    search_fields = ("city", "country_name", "path")
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp", "ip_hash", "country_code", "country_name", "city", "latitude", "longitude", "path", "device_type")