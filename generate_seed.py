"""
Generates data/02_seed.sql deterministically.

Design constraints (these are load-bearing for the blog post's claims):
  AS_OF = 2026-07-01, data runs 2023-01-01 .. 2026-06-30 (partial final year)
  - exactly 9 customers have no order in calendar 2026      (naive "lapsed")
  - exactly 4 customers have last_order < 2025-07-01        (correct trailing-12m "lapsed")
  - the 5 in between last ordered Sep/Oct 2025 and are high-value accounts
  - one order has NULL customer_id  (guest checkout -> breaks NOT IN)
  - one order has NULL amount       (COUNT(*) vs COUNT(amount) vs SUM)
  - ties on max amount within a customer, and a tie at rank 3 within a channel
  - one customer goes quiet for >18 months then returns
  - two customers have NULL city
"""
import random
from datetime import date, timedelta

random.seed(20260722)

AS_OF = date(2026, 7, 1)
START = date(2023, 1, 1)
END = date(2026, 6, 30)

CITIES = ["Toronto", "Copenhagen", "Montreal", "Aarhus", "Vancouver", "Malmo", "Calgary", "Odense"]
CHANNELS = ["web", "store", "partner", "marketplace"]
FIRST = ["Amir", "Sofie", "Elena", "Marcus", "Priya", "Jonas", "Nadia", "Rasmus", "Chen", "Isabel",
         "Tobias", "Leila", "Mikkel", "Grace", "Omar", "Freja", "Daniel", "Yuki", "Anders", "Rosa",
         "Kwame", "Lena", "Victor", "Maja", "Hassan", "Clara", "Emil", "Nina", "Theo", "Signe",
         "Ravi", "Astrid", "Luca", "Meera", "Soren", "Talia", "Nikolai", "Hana", "Felix", "Ingrid"]
LAST = ["Haddad", "Lund", "Petrova", "Nilsen", "Rao", "Berg", "Aziz", "Kjaer", "Wei", "Ferreira",
        "Holm", "Nasser", "Dahl", "Okafor", "Said", "Bruun", "Reyes", "Tanaka", "Vik", "Mendes",
        "Boateng", "Falk", "Ilic", "Strand", "Karim", "Moreau", "Rask", "Sole", "Papadakis", "Winther",
        "Kapoor", "Molin", "Bianchi", "Nair", "Toft", "Levi", "Orlov", "Sato", "Adler", "Storm"]

customers = []
for i in range(1, 41):
    city = CITIES[i % len(CITIES)]
    if i in (17, 33):
        city = None  # NULL city
    signup = START - timedelta(days=random.randint(0, 400))
    customers.append((i, f"{FIRST[i-1]} {LAST[i-1]}", city, signup))

# ---- cohort assignment -------------------------------------------------
NO_ORDERS = [35, 36, 37, 38, 39, 40]           # 6 customers, never ordered
TRULY_LAPSED = [1, 2, 3, 4]                    # last order well before 2025-07-01
TRAP = [5, 6, 7, 8, 9]                         # last order Sep/Oct 2025, high value
RETURNER = 10                                  # quiet 2023-08 .. 2025-11, back in 2026
ACTIVE = [c for c in range(10, 35)]            # 10..34 = 25 customers active in 2026

orders = []
oid = 1000


def rd(a, b):
    """random date between two dates, inclusive"""
    return a + timedelta(days=random.randint(0, (b - a).days))


def add(cid, d, amt, ch):
    global oid
    oid += 1
    orders.append((oid, cid, d, amt, ch))


# truly lapsed: activity 2023 -> early 2025, nothing after 2025-06-30
for cid in TRULY_LAPSED:
    last = rd(date(2024, 6, 1), date(2025, 6, 20))
    for _ in range(random.randint(3, 7)):
        add(cid, rd(START, last - timedelta(days=1)), round(random.uniform(40, 480), 2),
            random.choice(CHANNELS))
    add(cid, last, round(random.uniform(40, 300), 2), random.choice(CHANNELS))

# trap group: high volume, high value, last order Sep/Oct 2025
trap_last = [date(2025, 9, 12), date(2025, 9, 28), date(2025, 10, 3),
             date(2025, 10, 17), date(2025, 10, 29)]
for cid, last in zip(TRAP, trap_last):
    for _ in range(random.randint(14, 20)):
        add(cid, rd(START, last - timedelta(days=1)), round(random.uniform(300, 1900), 2),
            random.choice(CHANNELS))
    add(cid, last, round(random.uniform(400, 1200), 2), random.choice(CHANNELS))

# active customers: at least one order in H1 2026
for cid in ACTIVE:
    if cid == RETURNER:
        # early burst, long silence, then reactivation
        for _ in range(4):
            add(cid, rd(date(2023, 1, 5), date(2023, 8, 20)), round(random.uniform(60, 500), 2),
                random.choice(CHANNELS))
        for _ in range(3):
            add(cid, rd(date(2026, 1, 10), date(2026, 6, 25)), round(random.uniform(80, 700), 2),
                random.choice(CHANNELS))
        continue
    n = random.randint(4, 16)
    for _ in range(n):
        add(cid, rd(START, date(2025, 12, 31)), round(random.uniform(50, 1400), 2),
            random.choice(CHANNELS))
    for _ in range(random.randint(1, 2)):
        add(cid, rd(date(2026, 1, 1), END), round(random.uniform(50, 1400), 2),
            random.choice(CHANNELS))

# ---- deliberate edge cases --------------------------------------------
# 1. exact tie on a customer's largest order (ROW_NUMBER vs RANK diverge)
add(12, date(2026, 2, 11), 1750.00, "web")
add(12, date(2026, 4, 23), 1750.00, "store")

# 2. tie at rank 3 within the 'partner' channel (top-3 returns 4 rows under RANK)
add(21, date(2026, 3, 5), 2100.00, "partner")
add(22, date(2026, 3, 6), 2050.00, "partner")
add(23, date(2026, 3, 7), 2000.00, "partner")
add(24, date(2026, 3, 8), 2000.00, "partner")

# 3. guest checkout: NULL customer_id -> poisons NOT IN
add(None, date(2026, 5, 14), 219.99, "web")

# 4. NULL amount -> COUNT(*) != COUNT(amount), SUM skips it
add(19, date(2026, 6, 2), None, "store")

# 5. pin the last order to the close of the partial year
add(28, date(2026, 6, 30), 412.50, "web")

orders.sort(key=lambda r: (r[2], r[0]))
orders = [(i + 1, r[1], r[2], r[3], r[4]) for i, r in enumerate(orders)]


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, date):
        return f"'{v.isoformat()}'"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return str(v)


lines = []
lines.append("-- Seed data for sql-patterns. Generated deterministically; do not hand-edit.")
lines.append("-- Reference date for every exercise: 2026-07-01. The data ends 2026-06-30.")
lines.append("")
lines.append("INSERT INTO customers (customer_id, name, city, signup_date) VALUES")
lines.append(",\n".join(
    "  (" + ", ".join(q(v) for v in c) + ")" for c in customers) + ";")
lines.append("")
lines.append("INSERT INTO orders (order_id, customer_id, order_date, amount, channel) VALUES")
lines.append(",\n".join(
    "  (" + ", ".join(q(v) for v in o) + ")" for o in orders) + ";")

import os
os.makedirs("sql-patterns/data", exist_ok=True)
with open("sql-patterns/data/02_seed.sql", "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"customers: {len(customers)}  orders: {len(orders)}")
