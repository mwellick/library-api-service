import os
import stripe
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from django.urls import reverse
from dotenv import load_dotenv
from .models import Payment
from .calculations import (
    calculate_borrowing_amount,
    borrow_days,
    calculate_fine
)

load_dotenv()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


@transaction.atomic()
def create_payment_session(borrowing, amount, payment_type):
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(amount * 100),
                    "product_data": {
                        "name": borrowing.book.title,
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=settings.BASE_URL
        + reverse("payments:payment-success")
        + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=settings.BASE_URL + reverse("payments:payment-cancel"),
    )

    session_id = checkout_session.id
    session_url = checkout_session.url

    Payment.objects.create(
        status=Payment.Status.PENDING,
        type=payment_type,
        borrowing=borrowing,
        session_url=session_url,
        session_id=session_id,
        money_to_pay=amount,
    )

    return JsonResponse({"id": checkout_session.id})


@transaction.atomic()
def create_checkout_session(borrowing):
    days_of_borrow = borrow_days(
        borrowing.borrow_date,
        borrowing.expected_return_date,
    )
    total_price = calculate_borrowing_amount(
        days_of_borrow,
        borrowing.book.daily_fee
    )
    return create_payment_session(borrowing, total_price, Payment.Type.PAYMENT)


@transaction.atomic()
def create_fine_payment(borrowing):
    fine = calculate_fine(
        borrowing.expected_return_date,
        borrowing.actual_return_date,
        borrowing.book.daily_fee,
    )
    return create_payment_session(borrowing, fine, Payment.Type.FINE)
