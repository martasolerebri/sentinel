# 💷 Sentinel Finance Engine

> Ask your finances anything. Sentinel connects a conversational AI agent to your real transaction data.

🔗 **Live demo:** [martasolerebri.github.io/sentinel](https://martasolerebri.github.io/sentinel/)

> You'll need a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey) to use the chat.

---

*"How much did I spend on eating out last month?"*
*"What are my top 5 expenses this quarter?"*
*"Am I on track for my savings goal?"*
*"How does my financial health look?"*

Sentinel understands the question, picks the right tool, queries the database, and responds showing you exactly which tool it called. It remembers the conversation within the session, so follow-up questions just work.

---

## How It Works

The frontend is a static app built with HTML, Vanilla JS, and CSS. The backend is a FastAPI app that hosts the agent and serves the data from a SQLite database.

The core is a LangGraph reactive graph on top of `gemini-2.0-flash`. Two nodes, one cycle: the LLM decides whether a tool call is needed to answer the question; if so, it executes it and the result feeds back into the LLM which synthesises the final response. This gives precise control over how and when the database is consulted.

Conversation memory is handled by LangGraph's `MemorySaver` checkpointer, which persists the message list across turns within a session keyed by `user_id`. The compiled graph is cached per API key to avoid rebuilding it on every request.

The agent has **5 tools**:

| Tool | What it does |
|---|---|
| `analyze_spending` | Spending by category + income/savings balance for a period |
| `get_category_trend` | Monthly time series for a specific category over N months |
| `get_top_expenses` | Top N transactions, with automatic anomaly flags for anything 2× the category average |
| `check_savings_goal` | Goal progress, days remaining, and daily rate needed to hit the deadline |
| `get_financial_health` | Debt-to-income ratio + 50/30/20 rule breakdown with a plain-English verdict |

All periods are rolling windows from today: `week`, `month`, `quarter`, `half-year`, `year`.

---

## Data and Design Decisions

### Synthetic data for the demo

The demo doesn't use real bank data. `generate_data.py` produces synthetic transactions simulating a realistic UK user profile: supermarkets (Tesco, Sainsbury's, Lidl), restaurants (Deliveroo, Uber Eats, Starbucks), recurring subscriptions, a monthly salary, and housing costs. Intentional noise is added — misspelled merchants, duplicates, ambiguous categories — so the categorisation pipeline has something real to work with. `categorize.py` then uses Gemini to label each merchant into one of 10 categories.

This means the agent always works on the same static dataset — what you see in the demo is the same for everyone.

### Why not real Open Banking

In production, the natural data source would be **Open Banking**: the PSD2 standard requires European banks to expose APIs that allow, with explicit user consent, reading transactions and balances in real time.

Since the goal here is to demonstrate the reasoning layer, not data ingestion, we ruled this out. Synthetic data lets us focus on the agent architecture without distractions.

### Privacy and data security

**API key on the client.** The Gemini key is stored in `localStorage` and sent with every request. Acceptable for a personal demo — in production the key would never leave the server.

**Hugging Face Spaces.** The container is ephemeral: every restart regenerates the database from scratch. No conversation or financial data is persisted between sessions.

---

## Project Structure

```
sentinel/
├── Dockerfile                  # Build for Hugging Face Spaces
├── docs/
│   ├── index.html              # Main dashboard
│   ├── chat.html               # Full-page chat interface
│   ├── app.js                  # UI logic and Chart.js rendering
│   ├── api.js                  # Network layer (fetch to backend)
│   └── style.css               # Styles
│
└── backend/
    ├── app.py                  # FastAPI entrypoint + DB initialisation
    ├── config.py               # DB path, categories, period helpers
    ├── requirements.txt        # Python dependencies
    ├── agent/
    │   ├── graph.py            # LangGraph graph + per-key cache
    │   ├── tools.py            # 5 SQL tools for the agent
    │   └── state.py            # Typed graph state
    ├── api/
    │   └── routes.py           # REST endpoint definitions
    ├── scripts/
    │   ├── generate_data.py    # Synthetic transaction generator
    │   └── categorize.py       # Gemini-powered merchant categorisation
    └── data/
        └── finance.db          # SQLite (generated at runtime)
```

---

## Example Queries

- *"Where did most of my money go this month?"*
- *"Show me my grocery spending over the last 6 months"*
- *"What were my five biggest purchases this quarter?"*
- *"Am I on track to hit my savings goal?"*
- *"How does my financial health look right now?"*

---

## Author

[Marta Soler](https://github.com/martasolerebri) — Master's Degree Project

---

*Last Updated: March 2026*
