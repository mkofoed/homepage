from django.contrib import admin

from .models import SpotPrice


@admin.register(SpotPrice)
class SpotPriceAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "price_dkk", "price_eur")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp", "price_dkk", "price_eur")
