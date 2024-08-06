from django.db import models, transaction
from book.models import Book
from django.conf import settings


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @property
    def is_active(self) -> bool:
        return self.actual_return_date is None

    @staticmethod
    def can_borrow(
            book_inventory: int,
            book_title: str,
            book_cover: str,
            user_id: int,
            error_to_raise
    ):
        if book_inventory == 0:
            raise error_to_raise("This book is not currently available")
        if Borrowing.objects.filter(
                book__title=book_title,
                book__cover=book_cover,
                user_id=user_id,
                actual_return_date__isnull=True
        ).exists():
            raise error_to_raise("You have already borrowed this book and haven't returned it yet.")

        return {"book__inventory": book_inventory}

    def clean(self):
        Borrowing.can_borrow(
            self.book.inventory,
            self.book.title,
            self.book.cover,
            self.user.id,
            ValueError
        )

    @transaction.atomic()
    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        if not self.pk:
            if self.book.inventory == 0:
                raise ValueError("This book is not currently available")
            self.book.inventory -= 1
            self.book.save(update_fields=["inventory"])

        super(Borrowing, self).save(
            force_insert,
            force_update,
            using,
            update_fields
        )
