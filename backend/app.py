import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import DB_PATH

def init_db() -> None:
    """
    Creates tables if they don't exist.
    Runs once on startup to ensure the schema is ready regardless
    of whether the data scripts have been executed.

    Design note — goals table:
        The app supports ONE active savings goal at a time.
        The table uses a fixed id=1: POST /api/goal does DELETE + INSERT with id=1.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL,
                merchant TEXT    NOT NULL,
                amount   REAL    NOT NULL,
                category TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS goals (
                id             INTEGER PRIMARY KEY,
                name           TEXT    NOT NULL UNIQUE,
                target_amount  REAL    NOT NULL,
                current_amount REAL    NOT NULL DEFAULT 0,
                deadline       DATE    NOT NULL
            );
        """)
        conn.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialises the database on startup."""
    init_db()
    yield

app = FastAPI(
    title="Sentinel Finance Engine",
    description=(
        "Personal finance assistant API. "
        "The user's API key is passed per-request and never stored."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "https://martasolerebri.github.io",  
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/", tags=["health"])
def health_check():
    """API health check."""
    return {"status": "ok", "service": "Sentinel Finance Engine"}