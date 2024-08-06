from rest_framework import serializers
from .models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "expected_return_date"
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        Borrowing.can_borrow(
            attrs["book"].inventory,
            attrs["book"].title,
            attrs["book"].cover,
            user.id,
            serializers.ValidationError,
        )
        return attrs


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)
    user_id = serializers.CharField(source="user.pk", read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "user_id",
            "is_active"
        ]


class BorrowingRetrieveSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="user.pk", read_only=True)
    user_email = serializers.CharField(source="user.email",read_only=True)
    author = serializers.CharField(source="book.author", read_only=True)
    book = serializers.CharField(source="book.title", read_only=True)
    book_cover = serializers.CharField(source="book.cover", read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "borrow_date",
            "expected_return_date",
            "user_id",
            "user_email",
            "author",
            "book",
            "book_cover"

        ]
