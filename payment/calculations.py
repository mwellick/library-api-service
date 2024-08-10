from datetime import date

FINE_MULTIPLIER = 2


def borrow_days(
        borrow_date: date,
        expected_return_date: date
) -> int:
    return (expected_return_date - borrow_date).days


def calculate_borrowing_amount(
        days_of_borrow: int,
        book_daily_fee: float
) -> float:
    amount = days_of_borrow * book_daily_fee
    return round(amount, 2)


def calculate_fine(
        expected_return_date: date,
        overdue: date,
        book_daily_fee: float
) -> float:
    fine = 0.0
    days_late = (overdue - expected_return_date).days
    if days_late > 0:
        fine += days_late * (book_daily_fee * FINE_MULTIPLIER)

    return round(fine, 2)
