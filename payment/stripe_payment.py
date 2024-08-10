import os
import stripe
from django.db import transaction
from django.conf import settings
from django.urls import reverse
from dotenv import load_dotenv
from .models import Payment

load_dotenv()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


def create_checkout_session(borrowing):
    total_price = 2
    unit_amount = 2
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(unit_amount * 100),
                    "product_data": {
                        "name": borrowing.book.title,
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=settings.BASE_URL + reverse("payments:payment-success"),
        cancel_url=settings.BASE_URL + reverse("payments:payment-cancel"),
    )

    session_id = checkout_session.id
    session_url = checkout_session.url

    create_payment = Payment.objects.create(
        status=Payment.Status.PENDING,
        type=Payment.Type.PAYMENT,
        borrowing=borrowing,
        session_url=session_url,
        session_id=session_id,
        money_to_pay=total_price
    )

    return create_payment
