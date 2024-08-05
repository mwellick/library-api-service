from rest_framework import serializers
from .models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "user",
            "expected_return_date"
        ]


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)
    user = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "user"
        ]

class BorrowingRetrieveSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)
    user = serializers.CharField(source="user.email", read_only=True)
    author = serializers.CharField(source="book.author",read_only=True)
    class Meta:
        model = Borrowing
        fields = [
            "borrow_date",
            "expected_return_date",
            "user",
            "book",
            "author"

        ]