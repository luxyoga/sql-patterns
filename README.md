# sql-patterns

A practice database and 16 exercises for the eight SQL patterns that cover most analytics work.

Companion to the post *I Could Read Any SQL Query. I Just Couldn't Write One.*

The point of this repo is the thing that closes the recall gap: a blank editor and a real
database. Reading solutions does not work. You already know that, or you would not be here.

## Quick start

```bash
git clone https://github.com/<you>/sql-patterns
cd sql-patterns
pip install duckdb
python load.py duckdb        # or: python load.py sqlite
duckdb practice.duckdb
```

Then open `exercises/EXERCISES.md` and start at question 1. Solutions live in
`solutions/SOLUTIONS.sql` — the whole exercise is worthless if you open that first.

## The schema

```
customers(customer_id, name, city, signup_date)      40 rows
orders(order_id, customer_id, order_date, amount, channel)   396 rows
```

Two tables, on purpose. Every pattern below is expressible against them, and a schema you can
hold in your head means you spend your attention on the query rather than on orientation.

## The eight patterns

| # | Pattern | Question sounds like |
|---|---------|----------------------|
| 1 | Filter and sort | top, largest, most recent — with no *per* and no *each* |
| 2 | Group and aggregate | per, for each, total, average, "at least 5" |
| 3 | Join to enrich | along with, including the name — a column that is not on the fact table |
| 4 | Anti-join | never, no, without, missing, yet to |
| 5 | Conditional aggregation | what share, how many of them, tier, bucket, side by side |
| 6 | Top N per group | *each* combined with *largest* / *latest* |
| 7 | Row to row | change, growth, running, cumulative, versus previous |
| 8 | Boundary date | churned, lapsed, retained, reactivated, cohort, first, last |

## The data is not clean, deliberately

Every one of these is seeded on purpose, because clean practice data teaches you to write
queries that fall over on contact with real tables:

- **A guest checkout** with `customer_id IS NULL`. It poisons `NOT IN` — the anti-join returns
  zero rows and gives you no hint why. `NOT EXISTS` handles it. This is exercise 7.
- **An order with `amount IS NULL`**, so `COUNT(*)`, `COUNT(amount)` and `SUM(amount)` disagree.
- **Ties.** One customer has two orders tied at their maximum, so `ROW_NUMBER` returns 34 rows
  and `RANK` returns 35. One channel has a tie at rank 3, so top-3 returns four rows under
  `RANK`. Neither is wrong; you have to decide which you meant.
- **Two customers with no city**, which vanish silently unless you `COALESCE` before grouping.
- **A customer who went quiet for 972 days and came back.** Most churn logic counts them as
  continuously active.
- **A partial final year.** The data stops on 2026-06-30, so a naive year-over-year comparison
  shows revenue collapsing by more than 40%. It has not. You are comparing six months to twelve.
- **The lapsed-customer trap.** Defining lapsed as "no order this calendar year" flags 9
  customers. Defining it as "last order more than twelve months ago" flags 4. The five in
  between last ordered in autumn 2025 and are among the highest-spending accounts in the
  business. Both queries run without error. Both return a plausible number. One of them puts
  your best customers on a win-back list. That is exercise 15, and it is the reason this repo
  exists.

## Reference date

Every exercise treats **2026-07-01** as today, and nothing uses `CURRENT_DATE`. The answers are
therefore stable forever — a repo whose expected results drift every month is worse than no
repo. If you want the rolling-window behaviour, substitute your own as-of date and the logic
holds.

## Verifying

```bash
python tests_verify.py
```

18 assertions covering every claim above, run in CI on each push. `generate_seed.py` rebuilds
`data/02_seed.sql` deterministically if you want to fork the dataset and change the shape.

## Dialects

Schema and seed load unmodified in DuckDB, SQLite, PostgreSQL and MySQL 8+. Solutions are
written in DuckDB / PostgreSQL syntax; `DIALECTS.md` has the four substitutions you need
elsewhere.
