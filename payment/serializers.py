from rest_framework import serializers
from borrowing.serializers import  BorrowingRetrieveSerializer
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay"
        ]


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.CharField(source="borrowing.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "borrowing_id",
            "money_to_pay"
        ]


class PaymentRetrieveSerializer(serializers.ModelSerializer):
    borrow_info = BorrowingRetrieveSerializer(source="borrowing")

    class Meta:
        model = Payment
        fields = [
            "status",
            "type",
            "money_to_pay",
            "borrow_info",

        ]
