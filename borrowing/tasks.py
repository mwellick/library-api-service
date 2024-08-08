from .models import Borrowing
from celery import shared_task
from django.utils import timezone
from tg_notifications.notifications import send_message


@shared_task()
def check_borrowings_overdue():
    now = timezone.now()
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lt=now, actual_return_date__isnull=True
    )

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"Overdue borrowing!\n"
                f"Borrow id: {borrowing.id}\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}, Author: {borrowing.book.author}, cover({borrowing.book.cover})\n,"
                f"User was supposed to return this book on {borrowing.expected_return_date}"
            )
            send_message(message)
    else:
        send_message("No borrowings overdue today!")
