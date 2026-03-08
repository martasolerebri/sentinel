from datetime import date, timedelta
from pathlib import Path

from dateutil.relativedelta import relativedelta

DB_PATH: Path = Path(__file__).parent / "data" / "finance.db"

VALID_PERIODS: frozenset[str] = frozenset(
    {"week", "month", "quarter", "half-year", "year"}
)

CATEGORIES = [
    "Housing",
    "Groceries",
    "Eating Out",
    "Transport",
    "Entertainment",
    "Utilities",
    "Subscriptions",
    "Health",
    "Shopping",
    "Other",
]

def period_start(period: str) -> date:
    """
    Returns the start date of a rolling window ending today.

        week      → last 7 days
        month     → last 30 days
        quarter   → last 3 months
        half-year → last 6 months
        year      → last 12 months

    Raises ValueError for unknown periods.
    """
    if period not in VALID_PERIODS:
        raise ValueError(
            f"Invalid period: '{period}'. Use one of: {', '.join(sorted(VALID_PERIODS))}"
        )
    today = date.today()
    if period == "week":
        return today - timedelta(weeks=1)
    elif period == "month":
        return today - relativedelta(months=1)
    elif period == "quarter":
        return today - relativedelta(months=3)
    elif period == "half-year":
        return today - relativedelta(months=6)
    else:  
        return today - relativedelta(years=1)