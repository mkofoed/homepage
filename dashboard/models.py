from django.db import models


class SpotPrice(models.Model):
    timestamp = models.DateTimeField(
        primary_key=True,
        help_text="The hour the price applies to (HourDK)",
    )
    price_dkk = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in DKK per MWh",
    )
    price_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in EUR per MWh",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.price_dkk} DKK"


class SpotPriceHourly(models.Model):
    """Read-only model backed by TimescaleDB continuous aggregate."""

    bucket = models.DateTimeField(primary_key=True)
    price_area = models.CharField(max_length=10)
    avg_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    avg_price_eur = models.DecimalField(max_digits=12, decimal_places=6)
    min_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    max_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    sample_count = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = "dashboard_spotprice_hourly"
        ordering = ["-bucket"]

    def __str__(self) -> str:
        return f"{self.price_area} {self.bucket:%Y-%m-%d %H:00} avg={self.avg_price_dkk}"
