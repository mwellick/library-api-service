from rest_framework import serializers
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
            "session_url",
            "session_id",
            "borrowing_id",
            "money_to_pay"
        ]


class PaymentRetrieveSerializer(serializers.ModelSerializer):
    borrow_info = serializers.CharField(source="borrowing", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "status",
            "type",
            "money_to_pay",
            "session_url",
            "session_id",
            "borrow_info",

        ]
