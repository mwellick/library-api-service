from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = ("Hard", "hard")
        SOFT = ("Soft", "soft")

    title = models.CharField(max_length=63)
    author = models.CharField(max_length=63)
    cover = models.CharField(max_length=4, choices=CoverType.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.title},author - {self.author},cover type - {self.cover}"
