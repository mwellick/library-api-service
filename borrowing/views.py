import logging
from django.utils import timezone
from rest_framework import status
from django.db import transaction
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingRetrieveSerializer,
    ReturnBookSerializer
)
from .models import Borrowing
from tg_notifications.notifications import send_message


class BorrowingViewSet(ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)
        message = (f"New borrowing has been created\n"
                   f"Borrow id: {borrowing.id}\n"
                   f"Author: {borrowing.book.author}\n"
                   f"Book: {borrowing.book.title} (cover: {borrowing.book.cover})\n"
                   f"User: {borrowing.user.email}\n"
                   f"Return date {borrowing.expected_return_date}\n"
                   f"Daily fee {borrowing.book.daily_fee}$")

        send_message(message)

    def get_queryset(self):
        queryset = self.queryset
        status = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        if status:
            if status.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif status.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if not self.request.user.is_staff:
            queryset = self.queryset.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            return queryset.select_related("book", "user")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        elif self.action == "retrieve":
            return BorrowingRetrieveSerializer
        elif self.action == "return_book":
            return ReturnBookSerializer
        return BorrowingSerializer

    logging.debug("Starting...")

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="return"
    )
    @transaction.atomic()
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "You have already returned this book"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(
            borrowing,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        book = borrowing.book
        book.inventory += 1
        borrowing.actual_return_date = timezone.now()
        borrowing.save()
        book.save()
        message = (f"{borrowing.user.email} has returned book "
                   f"{borrowing.book.title}(cover: {borrowing.book.cover}) "
                   f"from {borrowing.borrow_date}\n"
                   f"Borrowing id: {borrowing.id}\n"
                   f"Return date: {borrowing.actual_return_date}")
        send_message(message)
        return Response(serializer.data, status=status.HTTP_200_OK)
