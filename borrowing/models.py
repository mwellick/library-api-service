from django.db import models
from book.models import Book
from django.conf import settings


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @staticmethod
    def can_borrow(
            book_inventory: int,
            book_title: str,
            book_cover: str,
            error_to_raise
    ):
        if book_inventory == 0:
            raise error_to_raise("This book is not currently available")
        if Borrowing.objects.filter(
                book__title=book_title,
                book__cover=book_cover,
                actual_return_date__isnull=True
        ).exists():
            raise error_to_raise("You have already borrowed this book and haven't returned it yet.")

        return {"book__inventory": book_inventory}

    def clean(self):
        Borrowing.can_borrow(
            self.book.inventory,
            self.book.title,
            self.book.cover,
            ValueError
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None
    ):
        self.full_clean()
        super(Borrowing, self).save(
            force_insert,
            force_update,
            using,
            update_fields
        )
