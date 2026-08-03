import duckdb, sqlite3, sys

schema = open("data/01_schema.sql").read()
seed = open("data/02_seed.sql").read()

con = duckdb.connect()
con.execute(schema)
con.execute(seed)


def one(sql):
    return con.execute(sql).fetchone()[0]


checks = []


def check(label, got, want):
    checks.append((label, got, want, got == want))


# --- the headline claim -------------------------------------------------
naive = one("""
SELECT COUNT(*) FROM (
  SELECT customer_id FROM orders WHERE customer_id IS NOT NULL
  GROUP BY customer_id
  HAVING MAX(order_date) < DATE '2026-01-01')""")
correct = one("""
SELECT COUNT(*) FROM (
  SELECT customer_id FROM orders WHERE customer_id IS NOT NULL
  GROUP BY customer_id
  HAVING MAX(order_date) < DATE '2025-07-01')""")
check("naive lapsed (no order in calendar 2026)", naive, 9)
check("correct lapsed (last order < AS_OF - 12 months)", correct, 4)
check("the gap between them", naive - correct, 5)

# the 5 in between are genuinely high-value
rank_of_trap = one("""
WITH lifetime AS (
  SELECT customer_id, SUM(amount) AS ltv FROM orders
  WHERE customer_id IS NOT NULL GROUP BY customer_id),
ranked AS (SELECT customer_id, ROW_NUMBER() OVER (ORDER BY ltv DESC) rn FROM lifetime)
SELECT MAX(rn) FROM ranked WHERE customer_id BETWEEN 5 AND 9""")
check("worst lifetime-value rank among the 5 false positives (of 34)", rank_of_trap <= 12, True)

# --- structural edge cases ---------------------------------------------
check("customers", one("SELECT COUNT(*) FROM customers"), 40)
check("customers who never ordered", one("""
  SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)"""), 6)
check("orders with NULL customer_id (guest checkout)",
      one("SELECT COUNT(*) FROM orders WHERE customer_id IS NULL"), 1)
check("NOT IN is poisoned by that NULL -> returns 0 rows", one("""
  SELECT COUNT(*) FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM orders)"""), 0)
check("orders with NULL amount", one("SELECT COUNT(*) FROM orders WHERE amount IS NULL"), 1)
check("COUNT(*) != COUNT(amount)",
      one("SELECT COUNT(*) FROM orders") != one("SELECT COUNT(amount) FROM orders"), True)
check("customers with NULL city", one("SELECT COUNT(*) FROM customers WHERE city IS NULL"), 2)

# ties: ROW_NUMBER vs RANK diverge
rn = one("""
WITH r AS (SELECT customer_id, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) k
           FROM orders WHERE customer_id IS NOT NULL)
SELECT COUNT(*) FROM r WHERE k = 1""")
rk = one("""
WITH r AS (SELECT customer_id, RANK() OVER (PARTITION BY customer_id ORDER BY amount DESC) k
           FROM orders WHERE customer_id IS NOT NULL)
SELECT COUNT(*) FROM r WHERE k = 1""")
check("ROW_NUMBER top-1 per customer", rn, 34)
check("RANK top-1 per customer (tie inflates it)", rk, 35)

top3 = one("""
WITH r AS (SELECT channel, RANK() OVER (PARTITION BY channel ORDER BY amount DESC) k
           FROM orders WHERE channel = 'partner')
SELECT COUNT(*) FROM r WHERE k <= 3""")
check("RANK top-3 in 'partner' returns 4 rows (tie at 3)", top3, 4)

# the customer who went quiet and came back
gap = one("""
WITH g AS (SELECT customer_id, order_date,
            LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) prev
           FROM orders WHERE customer_id IS NOT NULL)
SELECT MAX(order_date - prev) FROM g""")
check("longest silent gap exceeds 700 days", gap > 700, True)

# partial final year makes YoY look like a collapse
y25 = one("SELECT SUM(amount) FROM orders WHERE order_date BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'")
y26 = one("SELECT SUM(amount) FROM orders WHERE order_date >= DATE '2026-01-01'")
check("2026 revenue looks like a >40% collapse vs 2025", float(y26) < float(y25) * 0.6, True)
check("data ends 2026-06-30", str(one("SELECT MAX(order_date) FROM orders")), "2026-06-30")

# --- portability: the same two files must load in SQLite ----------------
try:
    lite = sqlite3.connect(":memory:")
    lite.executescript(schema)
    lite.executescript(seed)
    n = lite.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    check("schema + seed load unmodified in SQLite", n, one("SELECT COUNT(*) FROM orders"))
except Exception as e:
    check("schema + seed load unmodified in SQLite", f"ERROR {e}", "ok")

w = max(len(c[0]) for c in checks)
bad = 0
for label, got, want, ok in checks:
    if not ok:
        bad += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label:<{w}}  got={got!r} want={want!r}")
print(f"\n{len(checks) - bad}/{len(checks)} passed")
sys.exit(1 if bad else 0)
