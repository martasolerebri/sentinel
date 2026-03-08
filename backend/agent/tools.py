import sqlite3
from datetime import date

from dateutil.relativedelta import relativedelta
from langchain_core.tools import tool

from config import period_start, DB_PATH

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@tool
def analyze_spending(period: str) -> dict:
    """
    Returns spending by category AND the income/savings balance for the period.
    Use this when the user asks how much they spent, where their money went,
    or wants a general financial overview.

    Args:
        period: 'week' | 'month' | 'quarter' | 'half-year' | 'year'

    Returns a dict with:
        - spending_by_category: {category: total_gbp}  (positive amounts)
        - income: total income
        - total_spent: total outgoing
        - net_savings: income - total_spent
        - period: the period analysed
    """
    try:
        start = period_start(period)
    except ValueError as e:
        return {"error": str(e)}

    today = date.today()

    with _conn() as conn:
        cat_rows = conn.execute(
            """
            SELECT category, ROUND(ABS(SUM(amount)), 2) AS total
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category
            ORDER BY total DESC
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchall()

        income_row = conn.execute(
            """
            SELECT ROUND(SUM(amount), 2) AS income
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount > 0
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchone()

    by_cat = {r["category"]: r["total"] for r in cat_rows}
    income = float(income_row["income"] or 0)
    total_spent = sum(by_cat.values())

    return {
        "period": period,
        "spending_by_category": by_cat,
        "income": round(income, 2),
        "total_spent": round(total_spent, 2),
        "net_savings": round(income - total_spent, 2),
    }

@tool
def get_category_trend(category: str, months: int = 6) -> list[dict]:
    """
    Returns the monthly spending trend for a specific category over the last N months.
    Use when the user asks how a category has changed over time.

    Args:
        category: exact category name (e.g. 'Groceries', 'Eating Out', 'Transport')
        months:   how many months back to look (default 6)

    Returns a list of {"month": "YYYY-MM", "total": float} sorted oldest to newest.
    """
    start = date.today() - relativedelta(months=months)

    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT strftime('%Y-%m', date) AS month,
                   ROUND(ABS(SUM(amount)), 2) AS total
            FROM transactions
            WHERE category = ? AND date >= ? AND amount < 0
            GROUP BY month
            ORDER BY month ASC
            """,
            (category, start.isoformat()),
        ).fetchall()

    return [{"month": r["month"], "total": r["total"]} for r in rows]

@tool
def get_top_expenses(period: str, n: int = 5) -> list[dict]:
    """
    Returns the N largest individual transactions in the period.
    Automatically flags anomalies: transactions more than 2x the category average.
    Use when the user asks what their biggest spends were.

    Args:
        period: 'week' | 'month' | 'quarter' | 'half-year' | 'year'
        n:      number of results (default 5, max 20)

    Returns a list of dicts with merchant, amount, date, category, and anomaly flag.
    """
    try:
        start = period_start(period)
    except ValueError as e:
        return [{"error": str(e)}]

    today = date.today()
    n = min(max(n, 1), 20)

    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT merchant, ROUND(ABS(amount), 2) AS amount, date, category
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            ORDER BY ABS(amount) DESC
            LIMIT ?
            """,
            (start.isoformat(), today.isoformat(), n),
        ).fetchall()

        avg_rows = conn.execute(
            """
            SELECT category, ROUND(AVG(ABS(amount)), 2) AS avg_amount
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchall()

    cat_avg = {r["category"]: r["avg_amount"] for r in avg_rows}

    result = []
    for r in rows:
        avg = cat_avg.get(r["category"], 0)
        is_anomaly = avg > 0 and r["amount"] > avg * 2
        result.append({
            "merchant":  r["merchant"],
            "amount":    r["amount"],
            "date":      r["date"],
            "category":  r["category"],
            "anomaly":   is_anomaly,
        })

    return result

@tool
def check_savings_goal() -> dict:
    """
    Returns the current status of the active savings goal.
    Use when the user asks about their savings goal, target, or progress.

    Returns a dict with name, target, saved, remaining, deadline,
    days_remaining, percentage, and a plain-English on_track assessment.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT name, target_amount, current_amount, deadline FROM goals LIMIT 1"
        ).fetchone()

    if row is None:
        return {"error": "No savings goal defined yet. The user can create one in the dashboard."}

    today        = date.today()
    deadline     = date.fromisoformat(row["deadline"])
    days_left    = (deadline - today).days
    remaining    = round(row["target_amount"] - row["current_amount"], 2)
    percentage   = (
        round(row["current_amount"] / row["target_amount"] * 100, 1)
        if row["target_amount"] else 0
    )

    if days_left > 0 and remaining > 0:
        needed_per_day = round(remaining / days_left, 2)
        on_track_note  = f"Needs £{needed_per_day}/day to hit the deadline."
    elif remaining <= 0:
        on_track_note  = "Goal already reached!"
    else:
        on_track_note  = "Deadline has passed."

    return {
        "name":           row["name"],
        "target":         row["target_amount"],
        "saved":          row["current_amount"],
        "remaining":      remaining,
        "deadline":       row["deadline"],
        "days_remaining": days_left,
        "percentage":     percentage,
        "on_track":       on_track_note,
    }

@tool
def get_financial_health(months: int = 1) -> dict:
    """
    Comprehensive financial health check combining two frameworks:
      - Debt-to-income ratio (housing + debt / income). Healthy threshold 35%.
      - 50/30/20 rule breakdown (needs / wants / savings).

    Use when the user asks about their financial health, whether they are doing
    well financially, or wants to understand their spending habits.

    Args:
        months: period to analyse (1 = last month, 3 = quarter, 12 = year)
    """
    try:
        today = date.today()
        start = today - relativedelta(months=months)

        with _conn() as conn:
            income_row = conn.execute(
                "SELECT SUM(amount) AS total FROM transactions WHERE amount > 0 AND date >= ?",
                (start.isoformat(),),
            ).fetchone()
            income = float(income_row["total"] or 0)

            if income == 0:
                return {"error": f"No income found in the last {months} month(s)."}

            debt_row = conn.execute(
                """
                SELECT ABS(SUM(amount)) AS total FROM transactions
                WHERE amount < 0 AND date >= ?
                AND (
                    category = 'Housing'
                    OR LOWER(merchant) LIKE '%loan%'
                    OR LOWER(merchant) LIKE '%mortgage%'
                    OR LOWER(merchant) LIKE '%credit%'
                    OR LOWER(merchant) LIKE '%finance%'
                )
                """,
                (start.isoformat(),),
            ).fetchone()
            debt = float(debt_row["total"] or 0)

            needs_row = conn.execute(
                """
                SELECT ABS(SUM(amount)) AS total FROM transactions
                WHERE amount < 0 AND date >= ?
                AND category IN ('Housing', 'Groceries', 'Transport', 'Utilities', 'Health')
                """,
                (start.isoformat(),),
            ).fetchone()
            needs = float(needs_row["total"] or 0)

            wants_row = conn.execute(
                """
                SELECT ABS(SUM(amount)) AS total FROM transactions
                WHERE amount < 0 AND date >= ?
                AND category IN ('Eating Out', 'Entertainment', 'Subscriptions', 'Shopping', 'Other')
                """,
                (start.isoformat(),),
            ).fetchone()
            wants = float(wants_row["total"] or 0)

        savings    = income - needs - wants
        debt_ratio = (debt / income) * 100

        pct_needs   = round((needs / income) * 100, 1)
        pct_wants   = round((wants / income) * 100, 1)
        pct_savings = round((savings / income) * 100, 1)

        debt_status = "healthy" if debt_ratio <= 35 else "over-stretched"

        verdict_parts = []
        if debt_ratio > 35:
            verdict_parts.append(f"debt-to-income ratio is {round(debt_ratio,1)}% (limit: 35%)")
        if pct_needs > 50:
            verdict_parts.append(f"essential spending is {pct_needs}% of income (target 50%)")
        if pct_wants > 30:
            verdict_parts.append(f"discretionary spending is {pct_wants}% (target 30%)")
        if pct_savings < 20:
            verdict_parts.append(f"saving only {pct_savings}% (target 20%)")

        verdict = (
            "Finances look healthy across both frameworks. Keep it up!"
            if not verdict_parts
            else "Areas to watch: " + "; ".join(verdict_parts) + "."
        )

        return {
            "period_months": months,
            "income":        round(income, 2),
            "debt_ratio": {
                "status":           debt_status,
                "ratio_pct":        round(debt_ratio, 1),
                "threshold_pct":    35,
                "housing_and_debt": round(debt, 2),
            },
            "budget_50_30_20": {
                "needs_pct":   pct_needs,
                "wants_pct":   pct_wants,
                "savings_pct": pct_savings,
                "needs_gbp":   round(needs, 2),
                "wants_gbp":   round(wants, 2),
                "savings_gbp": round(savings, 2),
            },
            "verdict": verdict,
        }

    except Exception as e:
        return {"error": f"Internal error: {str(e)}"}

ALL_TOOLS = [
    analyze_spending,
    get_category_trend,
    get_top_expenses,
    check_savings_goal,
    get_financial_health,
]
