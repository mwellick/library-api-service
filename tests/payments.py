from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status
from book.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
from payment.serializers import PaymentSerializer, PaymentListSerializer

PAYMENT_URL = reverse("payments:payment-list")


def detail_url(payment_id: int) -> str:
    return reverse("borrowings:payment-detail", args=[payment_id])


class UnauthenticatedPaymentApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAndAdminUserPaymentTestView(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="test_psw1",
        )
        self.user_2 = get_user_model().objects.create_user(
            email="other_user@test.com",
            password="test_psw2",
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.book_1 = Book.objects.create(
            title="Test book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=2,
            daily_fee=0.5

        )
        self.borrowing_1 = Borrowing.objects.create(
            expected_return_date=timezone.now() + timedelta(days=1),
            book=self.book_1,
            user=self.user

        )
        self.borrowing_2 = Borrowing.objects.create(
            expected_return_date=timezone.now() - timedelta(days=2),
            book=self.book_1,
            user=self.user_2,
            actual_return_date=timezone.now() - timedelta(days=1)

        )
        self.payment_1 = Payment.objects.create(
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
            borrowing=self.borrowing_1,
            money_to_pay=2.0
        )
        self.payment_2 = Payment.objects.create(
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
            borrowing=self.borrowing_2,
            money_to_pay=3.0
        )

    def test_have_not_access_to_all_payments(self) -> None:
        payments = Payment.objects.filter(borrowing__user=self.user)
        serializer = PaymentListSerializer(payments, many=True)
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(len(res.data["results"]), payments.count())

    def test_admin_has_access_to_all_payments(self) -> None:
        self.client.force_authenticate(user=self.user_2)
        payments = Payment.objects.all()
        serializer = PaymentListSerializer(payments, many=True)
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(len(res.data["results"]), payments.count())
