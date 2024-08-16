from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status
from book.models import Book
from book.serializers import BookRetrieveSerializer

BOOK_URL = reverse("books:book-list")


def detail_url(book_id: int) -> str:
    return reverse("books:book-detail", args=[book_id])


class UnauthenticatedBookApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.book_1 = Book.objects.create(
            title="Test book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=2,
            daily_fee=0.5

        )

    def test_unauthenticated_book_list(self) -> None:
        res = self.client.get(BOOK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Book.objects.count(), 1)

    def test_retrieve_unauthenticated_book(self) -> None:
        res = self.client.get(detail_url(self.book_1.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Test@test.test",
            password="Testpsw1",
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

    def test_create_book_forbidden(self) -> None:
        payload = {
            "title": "book title",
            "author": "author",
            "cover": "hard",
            "inventory": 5,
            "daily_fee": 0.8

        }
        res = self.client.post(BOOK_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_authenticated_book(self) -> None:
        res = self.client.get(detail_url(self.book_1.id))
        serializer = BookRetrieveSerializer(self.book_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_delete_book_forbidden(self) -> None:
        res = self.client.delete(detail_url(self.book_1.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Test@test.test",
            password="Testpsw1",
            is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.book_1 = Book.objects.create(
            title="Test book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=2,
            daily_fee=0.5

        )

    def test_create_book(self) -> None:
        payload = {
            "title": "New Book Title",
            "author": "New Author",
            "cover": Book.CoverType.HARD,
            "inventory": 5,
            "daily_fee": 1.00,
        }

        res = self.client.post(BOOK_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_auth_delete_book(self) -> None:
        res = self.client.delete(detail_url(self.book_1.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)
