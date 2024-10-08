from django.utils import timezone
from rest_framework import status
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from payment.calculations import calculate_fine
from payment.stripe_payment import create_checkout_session, create_fine_payment
from .serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingRetrieveSerializer,
    ReturnBookSerializer,
)
from payment.models import Payment
from .models import Borrowing
from tg_notifications.notifications import send_message


@extend_schema_view(
    create=extend_schema(
        summary="Create a borrowing",
        description="Authenticated user can create a borrowing "
                    "and system automatically creates a payment for created borrowing"
    ),
    retrieve=extend_schema(
        summary="Get a detailed info about specific borrowing",
        description="Authenticated user can get info about own borrowing",
    ),
    destroy=extend_schema(
        summary="Delete a borrowing",
        description="Admin can delete users borrowings",
    ),
)
class BorrowingViewSet(ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_permissions(self):
        if self.action in ["destroy"]:
            permission_classes = [IsAdminUser]
        elif self.action in ["create", "list", "retrieve", "return_book"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @transaction.atomic()
    def perform_create(self, serializer):
        user = self.request.user
        active_payment = Payment.objects.filter(
            borrowing__user=user, status=Payment.Status.PENDING
        )

        if active_payment.exists():
            raise ValidationError(
                "New borrowing forbidden. "
                "You have an uncompleted pending payment."
            )

        borrowing = serializer.save(user=user)
        create_checkout_session(borrowing)
        message = (
            f"New borrowing has been created\n"
            f"Borrow id: {borrowing.id}\n"
            f"Author: {borrowing.book.author}\n"
            f"Book: {borrowing.book.title} (cover: {borrowing.book.cover})\n"
            f"User: {borrowing.user.email}\n"
            f"Return date: {borrowing.expected_return_date}\n"
            f"Daily fee {borrowing.book.daily_fee}$"
        )

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

    @extend_schema(
        methods=["GET"],
        summary="Get list of all borrowings",
        description="Authenticated user can get a list of all borrowings",
        parameters=[
            OpenApiParameter(
                name="is_active",
                description="Filter by active_status",
                type=bool,
                examples=[OpenApiExample("Example")],
            ),
            OpenApiParameter(
                name="user_id",
                description="Filter by user id",
                type=int,
                examples=[OpenApiExample("Example")],
            ),
        ],

    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        borrowing = self.get_object()
        user = self.request.user

        if not user.is_staff and borrowing.user == user:
            return Response(
                {"attention": "You don't have permission "
                              "to change borrowing info"}
            )
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Get a specific borrowing for return",
        description="Authenticated user can get a list of all borrowings",
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="return",
    )
    @transaction.atomic()
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "You have already returned this book"},
                status=status.HTTP_400_BAD_REQUEST,
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

        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()
        book.save()

        if borrowing.actual_return_date > borrowing.expected_return_date:
            fine = calculate_fine(
                borrowing.expected_return_date,
                borrowing.actual_return_date,
                borrowing.book.daily_fee,
            )
            fine_message = (
                f"{borrowing.user.email} has returned book "
                f"{borrowing.book.title}(cover: {borrowing.book.cover}) "
                f"from {borrowing.borrow_date}\n"
                f"Borrowing id: {borrowing.id}\n"
                f"Return date: {borrowing.actual_return_date}\n"
                f"{borrowing.user.email} has to pay {fine}$ fine"
            )

            send_message(fine_message)
            create_fine_payment(borrowing)

            return Response({"attention": f"Please,pay {fine}$ fine"})
        else:
            message = (
                f"{borrowing.user.email} has returned book "
                f"{borrowing.book.title}(cover: {borrowing.book.cover}) "
                f"from {borrowing.borrow_date}\n"
                f"Borrowing id: {borrowing.id}\n"
                f"Return date: {borrowing.actual_return_date}"
            )
            send_message(message)

        return Response(
            {"detail": "Book returned in time, no fine required."},
            status=status.HTTP_200_OK,
        )
