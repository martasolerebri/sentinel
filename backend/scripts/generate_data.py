import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

END_DATE   = date(2026, 3, 5)
START_DATE = (END_DATE - timedelta(days=18 * 30)).replace(day=1)

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "transactions_raw.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

GROCERIES = [
    ("TESCO EXPRESS {city}",          -1, "groceries",  8,  35),
    ("TESCO SUPERSTORE {city}",        -1, "groceries", 35,  95),
    ("SAINSBURY'S LOCAL {n:04d}",      -1, "groceries", 10,  40),
    ("SAINSBURY'S {city}",             -1, "groceries", 30,  80),
    ("WAITROSE & PARTNERS {n:04d}",    -1, "groceries", 25,  75),
    ("LIDL GB {n:04d}",                -1, "groceries", 12,  45),
    ("ALDI STORES {n:04d}",            -1, "groceries", 10,  40),
    ("M&S FOOD {city}",                -1, "groceries", 15,  55),
    ("OCADO RETAIL LTD",               -1, "groceries", 45, 110),
    ("CO-OP FOOD {n:04d}",             -1, "groceries",  8,  30),
]

EATING_OUT = [
    ("DELIVEROO* {n:08d}",             -1, "eating_out", 12,  38),
    ("UBER EATS {n:08d}",              -1, "eating_out", 11,  35),
    ("JUST EAT {n:06d}",               -1, "eating_out", 10,  32),
    ("PRET A MANGER {n:04d}",          -1, "eating_out",  4,  12),
    ("LEON RESTAURANTS {n:04d}",       -1, "eating_out",  7,  15),
    ("NANDOS {city}",                  -1, "eating_out", 12,  28),
    ("WAGAMAMA {n:04d}",               -1, "eating_out", 14,  32),
    ("COSTA COFFEE {n:04d}",           -1, "eating_out",  3,   8),
    ("STARBUCKS {n:04d} GB",           -1, "eating_out",  4,  10),
    ("MCDONALDS {city}",               -1, "eating_out",  4,  12),
    ("DISHOOM {city}",                 -1, "eating_out", 18,  45),
    ("THE PUB AT {n:04d}",             -1, "eating_out",  8,  30),
]

TRANSPORT = [
    ("TFL TRAVEL CHARGE",              -1, "transport",  2,  12),
    ("TFL *AUTOLOAD",                  -1, "transport", 20,  40),
    ("NATIONAL RAIL {n:08d}",          -1, "transport", 15,  85),
    ("UBER *TRIP {n:08d}",             -1, "transport",  7,  28),
    ("BOLT.EU/R/ {n:08d}",             -1, "transport",  5,  20),
    ("SHELL {n:04d} GB",               -1, "transport", 45,  80),
    ("BP {n:04d} GB",                  -1, "transport", 40,  75),
    ("NCP PARKING {n:06d}",            -1, "transport",  4,  18),
    ("GREATER ANGLIA {n:8d}",          -1, "transport", 12,  60),
]

ENTERTAINMENT = [
    ("STEAM PURCHASE",                 -1, "entertainment",  4,  45),
    ("TICKETMASTER* {n:08d}",          -1, "entertainment", 20,  95),
    ("VUE CINEMA {city}",              -1, "entertainment",  8,  22),
    ("ODEON CINEMAS {n:04d}",          -1, "entertainment",  8,  20),
    ("WATERSTONES {n:04d}",            -1, "entertainment",  8,  25),
    ("AMAZON.CO.UK MARKETPLACE",       -1, "entertainment", 10,  65),
    ("NINTENDO ESHOP",                 -1, "entertainment",  7,  60),
    ("PLAYSTATION DIRECT",             -1, "entertainment",  8,  70),
    ("PAYPAL *GAMING {n:08d}",         -1, "entertainment",  5,  25),
]

UTILITIES = [
    ("BRITISH GAS {month}",            -1, "utilities", 35,  90),
    ("OCTOPUS ENERGY {month}",         -1, "utilities", 40,  95),
    ("THAMES WATER {month}",           -1, "utilities", 18,  40),
    ("EDF ENERGY {month}",             -1, "utilities", 38,  85),
    ("BT GROUP {month}",               -1, "utilities", 35,  55),
    ("SKY UK {month}",                 -1, "utilities", 45,  65),
    ("THREE MOBILE {month}",           -1, "utilities", 15,  30),
    ("VODAFONE LTD {month}",           -1, "utilities", 18,  35),
    ("EE MOBILE {month}",              -1, "utilities", 15,  32),
]

SUBSCRIPTIONS = [
    ("NETFLIX.COM",                    -1, "subscriptions", 17.99, 17.99),
    ("SPOTIFY AB",                     -1, "subscriptions", 11.99, 11.99),
    ("AMAZON PRIME GB",                -1, "subscriptions",  8.99,  8.99),
    ("APPLE.COM/BILL",                 -1, "subscriptions",  6.99,  6.99),
    ("GOOGLE ONE STORAGE",             -1, "subscriptions",  1.99,  1.99),
    ("MICROSOFT 365 {n:08d}",          -1, "subscriptions",  7.99,  7.99),
    ("DISNEY PLUS GB",                 -1, "subscriptions",  4.99,  4.99),
    ("YOUTUBE PREMIUM",                -1, "subscriptions", 13.99, 13.99),
    ("ADOBE INC {n:08d}",              -1, "subscriptions", 54.99, 54.99),
    ("DUOLINGO SUPER",                 -1, "subscriptions",  6.99,  6.99),
]

HEALTH = [
    ("BOOTS PHARMACY {n:04d}",         -1, "health",  5,  30),
    ("LLOYDS PHARMACY {n:04d}",        -1, "health",  4,  25),
    ("PURE GYM LTD {n:04d}",           -1, "health", 25,  30),
    ("ANYTIME FITNESS {n:04d}",        -1, "health", 30,  40),
    ("BUPA UK {month}",                -1, "health", 35,  65),
    ("SPECSAVERS {n:04d}",             -1, "health", 20,  85),
    ("NHS PRESCRIPTION",               -1, "health",  9,   9),
    ("HUSSLE PASSES {month}",          -1, "health", 20,  35),
]

SHOPPING = [
    ("ZARA {city}",                    -1, "shopping", 20,  95),
    ("H&M {city}",                     -1, "shopping", 15,  70),
    ("ASOS.COM",                       -1, "shopping", 18,  90),
    ("JOHN LEWIS {city}",              -1, "shopping", 25, 140),
    ("NEXT RETAIL LTD",                -1, "shopping", 20,  80),
    ("UNIQLO {city}",                  -1, "shopping", 15,  70),
    ("PRIMARK {city}",                 -1, "shopping", 10,  45),
    ("AMAZON.CO.UK {n:08d}",           -1, "shopping", 12, 120),
    ("IKEA {city}",                    -1, "shopping", 30, 200),
    ("THE BODY SHOP {n:04d}",          -1, "shopping",  8,  35),
]

CITIES = ["LONDON", "MANCHESTER", "BIRMINGHAM", "BRISTOL", "LEEDS"]

WEEKDAY_WEIGHTS = [0.7, 0.75, 0.85, 0.9, 1.3, 1.5, 1.2]

def fmt_merchant(template: str, d: date) -> str:
    return template.format(
        n=random.randint(0, 9999_9999),
        month=d.strftime("%m/%Y"),
        city=random.choice(CITIES),
    )

def weighted_date(year: int, month: int, last_day: int,
                  from_day: int = 1, to_day: int = None) -> date:
    """Pick a random date within the range, biased toward weekends."""
    to_day = to_day or last_day
    candidates = [date(year, month, d) for d in range(from_day, to_day + 1)]
    weights = [WEEKDAY_WEIGHTS[d.weekday()] for d in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]

def last_day_of(year: int, month: int) -> int:
    if month == 12:
        return (date(year + 1, 1, 1) - timedelta(days=1)).day
    return (date(year, month + 1, 1) - timedelta(days=1)).day

def generate_transactions() -> pd.DataFrame:
    rows = []
    current = START_DATE

    active_subs = random.sample(SUBSCRIPTIONS, random.randint(3, 6))

    while current <= END_DATE:
        year, month = current.year, current.month
        ld = last_day_of(year, month)

        def rdate(from_day=1, to_day=None, weighted=True):
            to_day = to_day or ld
            if weighted:
                return weighted_date(year, month, ld, from_day, min(to_day, ld))
            else:
                return date(year, month, random.randint(from_day, min(to_day, ld)))

        is_christmas = month == 12
        is_holiday   = month in (7, 8)   
        is_bonus     = month in (6, 12)  

        salary_base = round(random.gauss(3200, 60), 2)
        if is_bonus:
            salary_base += round(random.gauss(1500, 80), 2)
        rows.append({
            "Date": date(year, month, min(25, ld)),
            "Merchant": f"BACS PAYMENT EMPLOYER LTD {month:02d}/{year}",
            "Amount": salary_base,
        })

        if random.random() < 0.25:
            rows.append({
                "Date": rdate(1, 10, weighted=False),
                "Merchant": f"MONZO SAVINGS POT {random.randint(10000, 99999)}",
                "Amount": round(random.uniform(50, 300), 2),
            })

        rent = round(random.gauss(1350, 15), 2)
        rows.append({
            "Date": rdate(1, 3, weighted=False),
            "Merchant": f"SO {month:02d}/{year} LANDLORD MGMT LTD",
            "Amount": -rent,
        })

        n_grocery = random.randint(4, 7)
        for _ in range(n_grocery):
            t = random.choice(GROCERIES)
            amt = round(random.uniform(t[3], t[4]), 2)
            if is_christmas:
                amt = round(amt * random.uniform(1.2, 1.5), 2)
            rows.append({"Date": rdate(), "Merchant": fmt_merchant(t[0], current), "Amount": -amt})

        n_eating = random.randint(3, 7)
        for _ in range(n_eating):
            t = random.choice(EATING_OUT)
            amt = round(random.uniform(t[3], t[4]), 2)
            rows.append({"Date": rdate(), "Merchant": fmt_merchant(t[0], current), "Amount": -amt})

        n_transport = random.randint(2, 5)
        for _ in range(n_transport):
            t = random.choice(TRANSPORT)
            amt = round(random.uniform(t[3], t[4]), 2)
            rows.append({"Date": rdate(), "Merchant": fmt_merchant(t[0], current), "Amount": -amt})

        n_ent = random.randint(1, 3)
        if is_christmas:
            n_ent += random.randint(1, 3) 
        for _ in range(n_ent):
            t = random.choice(ENTERTAINMENT)
            amt = round(random.uniform(t[3], t[4]), 2)
            rows.append({"Date": rdate(), "Merchant": fmt_merchant(t[0], current), "Amount": -amt})

        for t in random.sample(UTILITIES, random.randint(2, 4)):
            rows.append({
                "Date": rdate(1, 10, weighted=False),
                "Merchant": fmt_merchant(t[0], current),
                "Amount": -round(random.uniform(t[3], t[4]), 2),
            })

        for t in active_subs:
            rows.append({
                "Date": rdate(1, 15, weighted=False),
                "Merchant": fmt_merchant(t[0], current),
                "Amount": -t[3],
            })

        for _ in range(random.randint(0, 2)):
            t = random.choice(HEALTH)
            rows.append({"Date": rdate(), "Merchant": fmt_merchant(t[0], current), "Amount": -round(random.uniform(t[3], t[4]), 2)})

        n_shopping = random.randint(0, 2)
        if is_christmas:
            n_shopping += random.randint(2, 4)   
        for _ in range(n_shopping):
            t = random.choice(SHOPPING)
            amt = round(random.uniform(t[3], t[4]), 2)
            rows.append({"Date": rdate(), "Merchant": fmt_merchant(t[0], current), "Amount": -amt})

        if is_holiday and random.random() < 0.6:
            rows.append({
                "Date": rdate(1, 10, weighted=False),
                "Merchant": f"EASYJET {random.randint(10000000, 99999999)}",
                "Amount": -round(random.uniform(85, 280), 2),
            })
            rows.append({
                "Date": rdate(1, 10, weighted=False),
                "Merchant": f"BOOKING.COM {random.randint(10000000, 99999999)}",
                "Amount": -round(random.uniform(200, 600), 2),
            })

        if random.random() < 0.15:
            anomaly_merchants = [
                ("APPLE STORE {city}",         80, 400),
                ("CURRYS PC WORLD {city}",    150, 600),
                ("JOHN LEWIS {city}",         100, 450),
                ("AUTOTRADER PREMIUM",         50, 150),
                ("TRAINLINE {n:08d}",          60, 180),
                ("AIRBNB PAYMENTS",           120, 450),
            ]
            m, lo, hi = random.choice(anomaly_merchants)
            rows.append({
                "Date": rdate(),
                "Merchant": fmt_merchant(m, current),
                "Amount": -round(random.uniform(lo, hi), 2),
            })

        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = generate_transactions()
    df.to_csv(OUTPUT_PATH, index=False)

    n_rows    = len(df)
    n_months  = df["Date"].dt.to_period("M").nunique()
    total_in  = df[df["Amount"] > 0]["Amount"].sum()
    total_out = df[df["Amount"] < 0]["Amount"].sum()
    balance   = total_in + total_out

    print(f"\n✓ CSV saved to: {OUTPUT_PATH}")
    print(f"  Rows:     {n_rows}")
    print(f"  Months:   {n_months}")
    print(f"  Income:   £{total_in:,.2f}")
    print(f"  Spending: £{abs(total_out):,.2f}")
    print(f"  Balance:  £{balance:,.2f}  (~£{balance/n_months:,.0f}/month saved)")
    print("\nSample transactions:")
    print(df.head(12).to_string(index=False))