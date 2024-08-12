import os
import stripe
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from dotenv import load_dotenv
from .stripe_payment import create_checkout_session
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentRetrieveSerializer
)

load_dotenv()


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = self.queryset.filter(borrowing__user=self.request.user)
        if self.action in ("list", "retrieve"):
            return queryset.select_related("borrowing")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        elif self.action == "retrieve":
            return PaymentRetrieveSerializer
        return PaymentSerializer


class PaymentSuccessView(APIView):
    @transaction.atomic()
    def get(self, request, *args, **kwargs):
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
        session_id = self.request.query_params.get("session_id")

        retrieve_session = stripe.checkout.Session.retrieve(session_id)
        if retrieve_session.payment_status == "paid":
            payment = Payment.objects.get(session_id=session_id)
            if payment:
                payment.status = payment.Status.PAID
                payment.save()
        return Response(
            {
                "status": "Payment successful."
            },
            status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "Payment canceled.Please, complete your payment within 24 hours."
            },
            status=status.HTTP_200_OK
        )


class PaymentRenewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        payment = Payment.objects.filter(
            status="EXPIRED",
            borrowing__user=self.request.user
        ).first()
        if payment:
            create_checkout_session(
                payment.borrowing
            )
            return Response(
                {"status": "Your payment has successfully renewed"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"status": "No expired payments found"},
            status=status.HTTP_204_NO_CONTENT
        )
