from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentRetrieveSerializer
)


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
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "Payment successful."
            },
            status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "Payment canceled.Please, complete your payment within 24 hours."
            },
            status=status.HTTP_200_OK
        )
