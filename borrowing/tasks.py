from .models import Borrowing
from celery import shared_task
from django.utils import timezone
from tg_notifications.notifications import send_message
from payment.calculations import calculate_fine


@shared_task()
def check_borrowings_overdue():
    now = timezone.now().date()
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lt=now, actual_return_date__isnull=True
    )

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            fine_amount = calculate_fine(
                borrowing.expected_return_date,
                now,
                borrowing.book.daily_fee
            )
            message = (
                f"Overdue borrowing!\n"
                f"Borrow id: {borrowing.id}\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}, "
                f"Author: {borrowing.book.author}, "
                f"cover({borrowing.book.cover})\n,"
                f"User was supposed to return this book on "
                f"{borrowing.expected_return_date}\n"
                f"User has to pay {fine_amount}$ fine"
            )
            send_message(message)
    else:
        send_message("No borrowings overdue today!")
