"""
Synthetic data generator for the weekend-warehouse project.

Produces four CSV files under data/raw/ that mimic three source systems:

    raw_orders.csv          - e-commerce "app_db" orders (identified only by email)
    raw_customers.csv       - CRM customer records
    raw_tier_history.csv    - CRM tier change log (SCD2 source)
    raw_web_events.csv      - clickstream from website (anonymous + identified)

Deliberate real-world quirks:
    - Email casing varies across sources
    - ~10% of orders are guest checkouts (email not in CRM)
    - ~30% of customers have a tier upgrade
    - Web events: ~40% logged-in, ~5% start anonymous and stitch later
    - Some test/refund rows that need filtering in staging

Zero external dependencies (Python stdlib only).
Run: python data_generator/generate.py
"""

import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
SEED = 42
N_CUSTOMERS = 2000
N_ORDERS = 8000
N_EVENTS = 30000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 4, 30)

REGIONS = ["West", "Mountain", "Midwest", "South", "Northeast"]
CHANNELS = ["organic_search", "paid_search", "email", "social", "direct", "referral"]
EVENT_TYPES = ["page_view", "add_to_cart", "checkout_start", "checkout_complete", "search"]

OUT_DIR = Path(__file__).parent.parent / "data" / "raw"

FIRST_NAMES = ["Alex", "Priya", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley",
    "Avery", "Quinn", "Skyler", "Emerson", "Reese", "Drew", "Jamie", "Cameron",
    "Devon", "Hayden", "Kendall", "Logan", "Parker", "Rowan", "Sage", "Blair",
    "Maya", "Noor", "Wei", "Yuki", "Aiden", "Zoe", "Theo", "Luna", "Mateo",
    "Ezra", "Iris", "Owen", "Nora", "Felix", "Stella", "Kai", "Leo", "Mira",
    "Ravi", "Sana", "Diego", "Amara", "Elena", "Hana", "Ivan", "Julia"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez",
    "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott",
    "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nakamura",
    "Patel", "Khan", "Singh", "Cohen", "Rossi", "Mueller", "Kim", "Chen"]

EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com",
    "protonmail.com", "fastmail.com", "hey.com", "duck.com"]

URL_SEGMENTS = ["products", "category", "search", "cart", "account", "blog",
    "deals", "men", "women", "outerwear", "footwear", "accessories",
    "sale", "new", "guide", "support", "checkout", "wishlist"]


def fake_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def fake_email_for(name, suffix):
    parts = name.lower().replace(" ", ".")
    parts = "".join(ch for ch in parts if ord(ch) < 128)
    return f"{parts}{suffix}@{random.choice(EMAIL_DOMAINS)}"


def fake_uri_path(depth=2):
    return "/".join(random.choice(URL_SEGMENTS) for _ in range(depth))


random.seed(SEED)


def random_datetime(start, end):
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def jitter_email_case(email):
    r = random.random()
    if r < 0.70:
        return email.lower()
    if r < 0.90:
        local, domain = email.split("@")
        return local.title() + "@" + domain
    return email.upper()


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def gen_customers():
    customers = []
    for i in range(N_CUSTOMERS):
        signup = random_datetime(START_DATE, END_DATE - timedelta(days=30)).date()
        name = fake_name()
        customers.append({
            "crm_id": f"CRM{i:06d}",
            "email_canonical": fake_email_for(name, i),
            "full_name": name,
            "signup_date": signup,
            "region": random.choice(REGIONS),
            "acquisition_channel": random.choice(CHANNELS),
        })
    return customers


def write_raw_customers(customers):
    rows = [[c["crm_id"], jitter_email_case(c["email_canonical"]), c["full_name"],
             c["signup_date"].isoformat(), c["region"], c["acquisition_channel"]]
            for c in customers]
    write_csv(OUT_DIR / "raw_customers.csv",
              ["crm_id", "email", "full_name", "signup_date", "region", "acquisition_channel"],
              rows)


def write_raw_tier_history(customers):
    rows = []
    for c in customers:
        rows.append([c["crm_id"], "Bronze", c["signup_date"].isoformat()])
        if random.random() < 0.30:
            upgrade = c["signup_date"] + timedelta(days=random.randint(60, 600))
            if upgrade < END_DATE.date():
                tier1 = random.choice(["Silver", "Gold"])
                rows.append([c["crm_id"], tier1, upgrade.isoformat()])
                if tier1 == "Silver" and random.random() < 0.30:
                    upgrade2 = upgrade + timedelta(days=random.randint(60, 400))
                    if upgrade2 < END_DATE.date():
                        rows.append([c["crm_id"], "Gold", upgrade2.isoformat()])
    write_csv(OUT_DIR / "raw_tier_history.csv",
              ["crm_id", "tier", "valid_from"], rows)
    return len(rows)


def write_raw_orders(customers):
    customer_emails = [c["email_canonical"] for c in customers]
    rows = []
    for i in range(N_ORDERS):
        if random.random() < 0.90:
            email = random.choice(customer_emails)
        else:
            email = fake_email_for(fake_name(), 900000 + i)
        email = jitter_email_case(email)
        ts = random_datetime(START_DATE, END_DATE)
        gross = round(random.uniform(15, 350), 2)
        discount = round(gross * random.choice([0, 0, 0, 0.10, 0.20]), 2)
        net = round(gross - discount, 2)
        channel = random.choice(CHANNELS)
        r = random.random()
        if r < 0.02:
            status = "test"
        elif r < 0.03:
            status = "refunded"
            gross = -gross
            net = -net
            discount = 0.0
        else:
            status = random.choice(["completed", "completed", "completed", "shipped", "delivered"])
        rows.append([f"ORD{i:08d}", email, ts.isoformat(),
                     gross, discount, net, channel, status])
    write_csv(OUT_DIR / "raw_orders.csv",
              ["order_id", "customer_email", "order_timestamp",
               "gross_amount", "discount_amount", "net_amount",
               "channel", "status"], rows)


def write_raw_web_events(customers):
    customer_emails = [c["email_canonical"] for c in customers]
    anon_to_customer = {str(uuid.uuid4()): random.choice(customer_emails)
                        for _ in range(int(N_EVENTS * 0.05))}
    stitched = list(anon_to_customer.keys())
    rows = []
    for i in range(N_EVENTS):
        ts = random_datetime(START_DATE, END_DATE)
        session_id = uuid.uuid4().hex[:12]
        r = random.random()
        if r < 0.40:
            anon_id = str(uuid.uuid4())
            email = jitter_email_case(random.choice(customer_emails))
        elif r < 0.45 and stitched:
            anon_id = random.choice(stitched)
            email = (jitter_email_case(anon_to_customer[anon_id])
                     if random.random() < 0.5 else "")
        else:
            anon_id = str(uuid.uuid4())
            email = ""
        rows.append([f"EVT{i:09d}", anon_id, email,
                     random.choice(EVENT_TYPES), ts.isoformat(),
                     session_id, "/" + fake_uri_path(2)])
    write_csv(OUT_DIR / "raw_web_events.csv",
              ["event_id", "anonymous_id", "customer_email",
               "event_type", "event_timestamp", "session_id", "page_url"],
              rows)


def main():
    customers = gen_customers()
    write_raw_customers(customers)
    n_tier_rows = write_raw_tier_history(customers)
    write_raw_orders(customers)
    write_raw_web_events(customers)
    print(f"Wrote 4 CSVs to {OUT_DIR.resolve()}")
    print(f"  raw_customers.csv      : {N_CUSTOMERS:>6} rows")
    print(f"  raw_tier_history.csv   : {n_tier_rows:>6} rows  (SCD2 source)")
    print(f"  raw_orders.csv         : {N_ORDERS:>6} rows  (~10% guest, ~2% test, ~1% refund)")
    print(f"  raw_web_events.csv     : {N_EVENTS:>6} rows  (~40% identified)")


if __name__ == "__main__":
    main()
