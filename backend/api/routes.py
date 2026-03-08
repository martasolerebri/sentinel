import sqlite3
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from agent.graph import build_graph
from config import period_start, VALID_PERIODS, DB_PATH, CATEGORIES

MAX_MESSAGE_CHARS = 4_000

router = APIRouter(prefix="/api")

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _validate_period(period: str) -> None:
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Use one of: {', '.join(sorted(VALID_PERIODS))}",
        )

def _extract_api_key(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="API key required. Include header: Authorization: Bearer <your-key>",
        )
    key = authorization.removeprefix("Bearer ").strip()
    if not key:
        raise HTTPException(status_code=401, detail="Empty API key.")
    return key

def _goal_dict(row, today: date) -> dict:
    remaining   = round(row["target_amount"] - row["current_amount"], 2)
    percentage  = (
        round(row["current_amount"] / row["target_amount"] * 100, 1)
        if row["target_amount"] else 0
    )
    days_remaining = (date.fromisoformat(row["deadline"]) - today).days
    return {
        "id":             row["id"],
        "name":           row["name"],
        "target_amount":  row["target_amount"],
        "current_amount": row["current_amount"],
        "deadline":       row["deadline"],
        "remaining":      remaining,
        "percentage":     percentage,
        "days_remaining": days_remaining,
    }

class ChatMessage(BaseModel):
    message: str
    user_id: str

class GoalIn(BaseModel):
    name:           str
    target_amount:  float
    current_amount: float = 0.0
    deadline:       str   

@router.get("/dashboard")
def get_dashboard(period: str = Query(default="month")):
    """Spending by category for the period. Powers the donut chart."""
    _validate_period(period)
    today = date.today()
    start = period_start(period)

    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT category, ROUND(ABS(SUM(amount)), 2) AS total
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category ORDER BY total DESC
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchall()

    return {
        "period":               period,
        "spending_by_category": {r["category"]: r["total"] for r in rows},
    }

@router.get("/summary")
def get_summary(period: str = Query(default="month")):
    """Income vs spending balance for the period."""
    _validate_period(period)
    today = date.today()
    start = period_start(period)

    with _conn() as conn:
        row = conn.execute(
            """
            SELECT
                ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) AS income,
                ROUND(ABS(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END)), 2) AS spent
            FROM transactions
            WHERE date >= ? AND date <= ?
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchone()

    income = row["income"] or 0.0
    spent  = row["spent"]  or 0.0
    return {
        "income":  income,
        "spent":   spent,
        "savings": round(income - spent, 2),
    }

@router.get("/top-expenses")
def get_top_expenses(
    period: str = Query(default="month"),
    n: int = Query(default=5, ge=1, le=20),
):
    """Top N individual expenses, with anomaly flags."""
    _validate_period(period)
    today = date.today()
    start = period_start(period)

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

    return [
        {
            "merchant":  r["merchant"],
            "amount":    r["amount"],
            "date":      r["date"],
            "category":  r["category"],
            "anomaly":   cat_avg.get(r["category"], 0) > 0
                         and r["amount"] > cat_avg.get(r["category"], 0) * 2,
        }
        for r in rows
    ]

@router.get("/goal")
def get_goal():
    """Returns the active savings goal."""
    today = date.today()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, name, target_amount, current_amount, deadline FROM goals LIMIT 1"
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="No savings goal defined.")

    return _goal_dict(row, today)

@router.post("/goal", status_code=201)
def post_goal(goal: GoalIn):
    """Creates or replaces the savings goal."""
    try:
        date.fromisoformat(goal.deadline)
    except ValueError:
        raise HTTPException(status_code=400, detail="deadline must be YYYY-MM-DD.")

    if goal.target_amount <= 0:
        raise HTTPException(status_code=400, detail="target_amount must be greater than 0.")

    today = date.today()
    with _conn() as conn:
        conn.execute("DELETE FROM goals")
        conn.execute(
            """
            INSERT INTO goals (id, name, target_amount, current_amount, deadline)
            VALUES (1, :name, :target_amount, :current_amount, :deadline)
            """,
            goal.model_dump(),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, name, target_amount, current_amount, deadline FROM goals WHERE id = 1"
        ).fetchone()

    return _goal_dict(row, today)

@router.get("/insights")
def get_insights(
    period: str = Query(default="month"),
    api_key: str = Depends(_extract_api_key),
):
    """
    Generates a short AI-powered narrative digest for the period.
    Returns a plain-text summary with the most important observations.
    """
    _validate_period(period)
    today = date.today()
    start = period_start(period)

    with _conn() as conn:
        cat_rows = conn.execute(
            """
            SELECT category, ROUND(ABS(SUM(amount)), 2) AS total
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category ORDER BY total DESC
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchall()

        income_row = conn.execute(
            """
            SELECT ROUND(SUM(amount), 2) AS income FROM transactions
            WHERE date >= ? AND date <= ? AND amount > 0
            """,
            (start.isoformat(), today.isoformat()),
        ).fetchone()

        from dateutil.relativedelta import relativedelta
        period_days = (today - start).days
        prev_end   = start - relativedelta(days=1)
        prev_start = prev_end - relativedelta(days=period_days)

        prev_rows = conn.execute(
            """
            SELECT category, ROUND(ABS(SUM(amount)), 2) AS total
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category
            """,
            (prev_start.isoformat(), prev_end.isoformat()),
        ).fetchall()

    current_by_cat = {r["category"]: r["total"] for r in cat_rows}
    prev_by_cat    = {r["category"]: r["total"] for r in prev_rows}
    income         = float(income_row["income"] or 0)
    total_spent    = sum(current_by_cat.values())

    cat_lines = []
    for cat, amt in current_by_cat.items():
        prev = prev_by_cat.get(cat, 0)
        if prev > 0:
            change_pct = round((amt - prev) / prev * 100)
            direction  = f"+{change_pct}% vs prev period" if change_pct > 0 else f"{change_pct}% vs prev period"
        else:
            direction = "no prior data"
        cat_lines.append(f"  {cat}: £{amt:.2f} ({direction})")

    data_summary = "\n".join(cat_lines)

    prompt = (
        f"You are a friendly personal finance assistant. "
        f"Write a brief, punchy digest (3–4 sentences max) for the user's {period} spending. "
        f"Lead with the single most interesting or actionable observation. "
        f"Use £ for all amounts. Be direct and human — not robotic or list-y.\n\n"
        f"Data:\n"
        f"  Income: £{income:.2f}\n"
        f"  Total spent: £{total_spent:.2f}\n"
        f"  Net savings: £{income - total_spent:.2f}\n"
        f"Spending by category (vs previous {period}):\n{data_summary}"
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.5,
            google_api_key=api_key,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        narrative = response.content.strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(exc)}")

    return {
        "period":    period,
        "narrative": narrative,
        "income":    round(income, 2),
        "spent":     round(total_spent, 2),
        "savings":   round(income - total_spent, 2),
    }

@router.post("/chat")
def post_chat(
    body: ChatMessage,
    api_key: str = Depends(_extract_api_key),
):
    """
    Receives a user message and invokes the LangGraph agent.
    Conversation history is managed automatically by LangGraph MemorySaver
    using user_id as the thread_id.
    """
    if len(body.message) > MAX_MESSAGE_CHARS:
        raise HTTPException(
            status_code=422,
            detail=f"Message exceeds {MAX_MESSAGE_CHARS} character limit.",
        )

    config = {"configurable": {"thread_id": body.user_id}}

    try:
        graph  = build_graph(api_key)
        result = graph.invoke({"messages": [HumanMessage(content=body.message)]}, config)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent error: {str(exc)}")

    response = result["messages"][-1].content

    tool_used = None
    for msg in reversed(result["messages"]):
        if hasattr(msg, "name") and msg.name:
            tool_used = msg.name
            break

    return {
        "response": response,
        "tool_used": tool_used,
    }