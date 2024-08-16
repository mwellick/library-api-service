from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status
from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingListSerializer,
    BorrowingRetrieveSerializer
)

BORROWING_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id: int) -> str:
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


class UnauthenticatedBorrowingApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Test@test.test",
            password="Testpsw1",
            is_staff=False
        )
        self.user_2 = get_user_model().objects.create_user(
            email="user@test.test",
            password="Testpsw2",
            is_staff=False
        )
        self.client.force_authenticate(self.user)
        self.book_1 = Book.objects.create(
            title="Test book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=2,
            daily_fee=0.5

        )
        self.book_2 = Book.objects.create(
            title="Test another book",
            author="Test another Author",
            cover=Book.CoverType.SOFT,
            inventory=2,
            daily_fee=0.5

        )
        self.borrowing_1 = Borrowing.objects.create(
            expected_return_date=timezone.now() + timedelta(days=1),
            book=self.book_1,
            user=self.user

        )
        self.borrowing_2 = Borrowing.objects.create(
            expected_return_date=timezone.now() + timedelta(days=1),
            book=self.book_1,
            user=self.user_2

        )

    def test_borrowing_list(self) -> None:
        res = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.filter(user=self.user)
        serializer = BorrowingListSerializer(borrowings, many=True)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(len(res.data["results"]), borrowings.count())
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_borrowing_create(self) -> None:
        self.client.force_authenticate(self.user_2)
        payload = {
            "expected_return_date": (timezone.now() + timedelta(days=1)).date(),
            "book": self.book_2.id,
            "user": self.user_2.id
        }
        res = self.client.post(BORROWING_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_retrieve_borrowing(self) -> None:
        res = self.client.get(detail_url(self.borrowing_1.id))
        serializer = BorrowingRetrieveSerializer(self.borrowing_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_borrowing_info_forbidden(self) -> None:
        payload = {
            "expected_return_date": (timezone.now() + timedelta(days=3)).date(),
        }
        res = self.client.put(detail_url(self.borrowing_1.id), payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_borrowing_forbidden(self) -> None:
        res = self.client.delete(detail_url(self.borrowing_1.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_return_book(self):
        url = f"/api/borrowings/{self.borrowing_1.id}/return/"
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["detail"], "Book returned in time, no fine required.")
        self.assertEqual(self.book_1.inventory, 1)

    def test_already_returned_book(self):
        url = f"/api/borrowings/{self.borrowing_1.id}/return/"
        self.borrowing_1.actual_return_date = timezone.now().date()
        self.borrowing_1.save()
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["detail"],  "You have already returned this book")

    def test_return_book_late_with_fine(self):
        self.borrowing_1.expected_return_date = timezone.now() - timedelta(days=1)
        self.borrowing_1.save()
        url = f"/api/borrowings/{self.borrowing_1.id}/return/"
        res = self.client.post(url)
        self.borrowing_1.actual_return_date = timezone.now()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("Please,pay", res.data["attention"])
        self.assertIsNotNone(self.borrowing_1.actual_return_date)


class AdminBorrowingApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Test@test.test",
            password="Testpsw1",
            is_staff=True
        )
        self.user_2 = get_user_model().objects.create_user(
            email="user@test.test",
            password="Testpsw2",
            is_staff=False
        )
        self.client.force_authenticate(self.user)
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

    def test_filter_by_borrowing_status_true(self) -> None:
        url = "http://localhost:8000/api/borrowings/?is_active=true"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_by_borrowing_status_false(self) -> None:
        url = "http://localhost:8000/api/borrowings/?is_active=false"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_by_user_id(self) -> None:
        res = self.client.get(BORROWING_URL, data={"user_id": 1})
        serializer1 = BorrowingListSerializer(self.borrowing_1)
        serializer2 = BorrowingListSerializer(self.borrowing_2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_admin_borrowing_list(self) -> None:
        res = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingListSerializer(borrowings, many=True)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(len(res.data["results"]), borrowings.count())
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_borrowing_delete(self) -> None:
        res = self.client.delete(detail_url(self.borrowing_1.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 1)
