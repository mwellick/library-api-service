import os
import stripe
from celery import shared_task
from dotenv import load_dotenv
from .models import Payment

load_dotenv()


@shared_task()
def check_session_for_expiration():
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

    pending_payments = Payment.objects.filter(
        status=Payment.Status.PENDING
    )

    for payment in pending_payments:
        stripe_session = stripe.checkout.Session.retrieve(
            payment.session_id
        )
        if stripe_session.payment_status == "expired":
            payment.status = payment.Status.EXPIRED
            payment.save()
