from django.db import models


class PriceArea(models.TextChoices):
    DK1 = "DK1", "DK1 (West Denmark)"
    DK2 = "DK2", "DK2 (East Denmark)"


class SpotPrice(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(
        help_text="UTC timestamp for this price interval",
    )
    price_area = models.CharField(
        max_length=3,
        choices=PriceArea.choices,
        default=PriceArea.DK1,
        help_text="Price area: DK1 (West) or DK2 (East)",
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
        constraints = [
            models.UniqueConstraint(
                fields=["timestamp", "price_area"],
                name="uq_spotprice_timestamp_area",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.price_area} {self.timestamp} — {self.price_dkk} DKK"


class SpotPriceHourly(models.Model):
    """Read-only: TimescaleDB hourly continuous aggregate."""

    bucket = models.DateTimeField(primary_key=True)
    price_area = models.CharField(max_length=3)
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
        return f"{self.price_area} {self.bucket:%Y-%m-%d %H:00}"


class SpotPriceDaily(models.Model):
    """Read-only: TimescaleDB daily continuous aggregate."""

    bucket = models.DateTimeField(primary_key=True)
    price_area = models.CharField(max_length=3)
    avg_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    avg_price_eur = models.DecimalField(max_digits=12, decimal_places=6)
    min_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    max_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    sample_count = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = "dashboard_spotprice_daily"
        ordering = ["-bucket"]

    def __str__(self) -> str:
        return f"{self.price_area} {self.bucket:%Y-%m-%d}"


class SpotPriceMonthly(models.Model):
    """Read-only: TimescaleDB monthly continuous aggregate."""

    bucket = models.DateTimeField(primary_key=True)
    price_area = models.CharField(max_length=3)
    avg_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    avg_price_eur = models.DecimalField(max_digits=12, decimal_places=6)
    min_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    max_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    sample_count = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = "dashboard_spotprice_monthly"
        ordering = ["-bucket"]

    def __str__(self) -> str:
        return f"{self.price_area} {self.bucket:%Y-%m}"


class SpotPriceYearly(models.Model):
    """Read-only: TimescaleDB yearly continuous aggregate."""

    bucket = models.DateTimeField(primary_key=True)
    price_area = models.CharField(max_length=3)
    avg_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    avg_price_eur = models.DecimalField(max_digits=12, decimal_places=6)
    min_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    max_price_dkk = models.DecimalField(max_digits=12, decimal_places=6)
    sample_count = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = "dashboard_spotprice_yearly"
        ordering = ["-bucket"]

    def __str__(self) -> str:
        return f"{self.price_area} {self.bucket:%Y}"
