from django.db import models
from borrowing.models import Borrowing


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = ("Pending", "pending")
        PAID = ("Paid", "paid")
        EXPIRED = ("Expired", "expired")

    class Type(models.TextChoices):
        PAYMENT = ("Payment", "payment")
        FINE = ("Fine", "fine")

    status = models.CharField(max_length=7, choices=Status.choices)
    type = models.CharField(max_length=7, choices=Type.choices)
    borrowing = models.ForeignKey(
        Borrowing,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    session_url = models.URLField(null=True, blank=True)
    session_id = models.TextField(max_length=63, null=True, blank=True)
    money_to_pay = models.DecimalField(max_digits=5, decimal_places=2)
