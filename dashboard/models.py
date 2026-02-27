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
