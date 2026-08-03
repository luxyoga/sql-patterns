# Running this in something other than DuckDB

`data/01_schema.sql` and `data/02_seed.sql` are plain ANSI and load unmodified in DuckDB,
SQLite, PostgreSQL and MySQL 8+. No `SERIAL`, no `AUTOINCREMENT`, no vendor types, IDs are
supplied explicitly. That part is genuinely portable and is tested in CI against DuckDB and
SQLite on every push.

The **solutions** are written in DuckDB / PostgreSQL syntax. Four things need swapping
elsewhere. That is the whole list.

| What | DuckDB / PostgreSQL | SQLite | MySQL 8+ |
|---|---|---|---|
| Truncate to month | `DATE_TRUNC('month', order_date)` | `strftime('%Y-%m-01', order_date)` | `DATE_FORMAT(order_date, '%Y-%m-01')` |
| Days between dates | `end_date - start_date` | `julianday(end) - julianday(start)` | `DATEDIFF(end, start)` |
| Subtract 12 months | `DATE '2026-07-01' - INTERVAL '12 months'` | `date('2026-07-01','-12 months')` | `DATE_SUB('2026-07-01', INTERVAL 12 MONTH)` |
| Round a ratio | `ROUND(x, 1)` | `ROUND(x, 1)` (returns float) | `ROUND(x, 1)` |

Two further notes:

- **Window functions** need SQLite 3.25+ (2018) and MySQL 8.0+ (2018). On MySQL 5.7 patterns
  6 and 7 are not expressible as written, which is a decent argument for not learning on 5.7.
- **SQLite has no real DATE type.** Dates are stored as ISO strings. Ordering and `<`
  comparison still work correctly because ISO-8601 sorts lexicographically, which is the
  whole reason that format won.
