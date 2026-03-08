import os
import sqlite3
import textwrap
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

BASE_DIR   = Path(__file__).parent.parent
CSV_PATH   = BASE_DIR / "data" / "transactions_raw.csv"
DB_PATH    = BASE_DIR / "data" / "finance.db"

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

BATCH_SIZE  = 60
RETRY_DELAY = 3


def _build_prompt(merchants: list[str]) -> str:
    numbered = "\n".join(f"{i+1}. {m}" for i, m in enumerate(merchants))
    cats = ", ".join(CATEGORIES)
    return textwrap.dedent(f"""
        You are a UK personal finance categorizer.
        Classify each merchant into EXACTLY one of these categories:
        {cats}

        Rules:
        - Rent / landlord payments → Housing
        - Salary / BACS income → Other  (will be filtered separately)
        - Supermarkets, food shops → Groceries
        - Restaurants, cafés, takeaways, food delivery → Eating Out
        - TfL, trains, taxis, fuel, parking → Transport
        - Cinemas, games, books, concerts → Entertainment
        - Gas, electricity, water, broadband, mobile → Utilities
        - Netflix, Spotify, Adobe, recurring digital services → Subscriptions
        - Pharmacies, gym, dentist, NHS → Health
        - Clothing, electronics, general retail → Shopping
        - Anything else → Other

        Respond with ONLY a numbered list matching the input exactly:
        1. Category
        2. Category
        ...

        Merchants to classify:
        {numbered}
    """).strip()


def categorize_batch(client: genai.Client, merchants: list[str]) -> list[str]:
    prompt = _build_prompt(merchants)
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            lines = [l.strip() for l in response.text.strip().splitlines() if l.strip()]
            results = []
            for line in lines:
                if ". " in line:
                    cat = line.split(". ", 1)[1].strip()
                else:
                    cat = line.strip()
                results.append(cat if cat in CATEGORIES else "Other")
            while len(results) < len(merchants):
                results.append("Other")
            return results[:len(merchants)]
        except Exception as e:
            print(f"  ⚠ Attempt {attempt+1} failed: {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    return ["Other"] * len(merchants)


def run_categorization():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not set. Export it before running.")

    client = genai.Client(api_key=api_key)

    print(f"Loading transactions from {CSV_PATH}…")
    df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
    print(f"  {len(df)} rows loaded.")

    merchants = df["Merchant"].tolist()
    all_categories: list[str] = []

    total_batches = (len(merchants) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(merchants), BATCH_SIZE):
        batch = merchants[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} merchants)…")
        cats = categorize_batch(client, batch)
        all_categories.extend(cats)
        time.sleep(0.5)

    df["Category"] = all_categories

    df.to_csv(CSV_PATH, index=False)
    print(f"\n✓ Categories written to {CSV_PATH}")

    _write_db(df)
    print(f"✓ Database written to {DB_PATH}")

    print("\nCategory breakdown:")
    for cat, cnt in df["Category"].value_counts().items():
        spending = df[(df["Category"] == cat) & (df["Amount"] < 0)]["Amount"].sum()
        print(f"  {cat:<18} {cnt:>4} txns   £{abs(spending):>8,.2f}")


def _write_db(df: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute("""
        CREATE TABLE transactions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT NOT NULL,
            merchant TEXT NOT NULL,
            amount   REAL NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.execute("DROP TABLE IF EXISTS goals")
    conn.execute("""
        CREATE TABLE goals (
            id               INTEGER PRIMARY KEY,
            name             TEXT    NOT NULL,
            target_amount    REAL    NOT NULL,
            current_amount   REAL    NOT NULL DEFAULT 0,
            deadline         TEXT    NOT NULL
        )
    """)

    rows = [
        (
            row["Date"].strftime("%Y-%m-%d"),
            row["Merchant"],
            round(float(row["Amount"]), 2),
            row["Category"],
        )
        for _, row in df.iterrows()
    ]
    conn.executemany(
        "INSERT INTO transactions (date, merchant, amount, category) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    run_categorization()