-- Solutions for sql-patterns.
-- Written in DuckDB / PostgreSQL syntax. See DIALECTS.md for SQLite and MySQL.
-- Reference date throughout: 2026-07-01.

-- 1. The five largest orders  (pattern 1: Filter and sort)
-- expected: 5 rows; top amount is 2100.00
SELECT order_id, customer_id, amount
FROM   orders
ORDER  BY amount DESC
LIMIT  5;

-- 2. Most recent signups in Copenhagen  (pattern 1: Filter and sort)
-- expected: 3 rows
SELECT customer_id, name, signup_date
FROM   customers
WHERE  city = 'Copenhagen'
ORDER  BY signup_date DESC
LIMIT  3;

-- 3. Revenue by channel  (pattern 2: Group and aggregate)
-- expected: 4 rows
SELECT   channel,
         SUM(amount)          AS revenue,
         COUNT(*)             AS n_orders,
         ROUND(AVG(amount),2) AS avg_order
FROM     orders
GROUP BY channel
HAVING   COUNT(*) >= 50
ORDER BY revenue DESC;

-- 4. Heavy buyers  (pattern 2: Group and aggregate)
-- expected: 22 rows
SELECT   customer_id,
         COUNT(*)    AS n_orders,
         SUM(amount) AS lifetime_spend
FROM     orders
WHERE    customer_id IS NOT NULL
GROUP BY customer_id
HAVING   COUNT(*) >= 10
ORDER BY n_orders DESC;

-- 5. Put names on the biggest orders  (pattern 3: Join to enrich)
-- expected: 10 rows
SELECT o.order_id, c.name, c.city, o.amount, o.order_date
FROM   orders o
JOIN   customers c ON o.customer_id = c.customer_id
ORDER  BY o.amount DESC
LIMIT  10;

-- 6. Revenue by city  (pattern 3: Join to enrich)
-- expected: 9 rows, including an '(unknown)' bucket
SELECT   COALESCE(c.city, '(unknown)') AS city,
         COUNT(DISTINCT c.customer_id) AS customers,
         COALESCE(SUM(o.amount), 0)    AS revenue
FROM     customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY COALESCE(c.city, '(unknown)')
ORDER BY revenue DESC;

-- 7. Customers who have never ordered  (pattern 4: Anti-join (the absence pattern))
-- expected: 6 rows -- and the NOT IN version returns 0, which is the point
SELECT customer_id, name, city
FROM   customers c
WHERE  NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)
ORDER  BY customer_id;

-- 8. Ordered in 2025, gone in 2026  (pattern 4: Anti-join (the absence pattern))
-- expected: 7 rows
SELECT c.customer_id, c.name
FROM   customers c
WHERE  EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
                 AND o.order_date >= DATE '2025-01-01' AND o.order_date < DATE '2026-01-01')
  AND  NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
                 AND o.order_date >= DATE '2026-01-01')
ORDER  BY c.customer_id;

-- 9. Large-order share by channel  (pattern 5: Conditional aggregation)
-- expected: 4 rows
SELECT   channel,
         COUNT(*)                                              AS n_orders,
         SUM(CASE WHEN amount >= 1000 THEN 1 ELSE 0 END)       AS large_orders,
         ROUND(100.0 * SUM(CASE WHEN amount >= 1000 THEN 1 ELSE 0 END)
               / NULLIF(COUNT(*), 0), 1)                       AS pct_large
FROM     orders
GROUP BY channel
ORDER BY pct_large DESC;

-- 10. Bucket customers by lifetime value  (pattern 5: Conditional aggregation)
-- expected: 3 tiers
WITH lifetime AS (
    SELECT   customer_id, SUM(amount) AS ltv
    FROM     orders
    WHERE    customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT   CASE WHEN ltv >= 5000 THEN 'Major'
              WHEN ltv >= 1500 THEN 'Mid'
              ELSE 'Standard' END AS tier,
         COUNT(*)    AS customers,
         SUM(ltv)    AS revenue
FROM     lifetime
GROUP BY 1
ORDER BY revenue DESC;

-- 11. Each customer's largest order  (pattern 6: Top N per group)
-- expected: 34 rows with ROW_NUMBER, 35 with RANK -- the extra row is the tie
WITH ranked AS (
    SELECT order_id, customer_id, amount, order_date,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY amount DESC, order_id) AS rn
    FROM   orders
    WHERE  customer_id IS NOT NULL
)
SELECT order_id, customer_id, amount, order_date
FROM   ranked
WHERE  rn = 1
ORDER  BY amount DESC;

-- 12. Top three orders per channel  (pattern 6: Top N per group)
-- expected: 13 rows with RANK, 12 with ROW_NUMBER -- 'partner' has a tie at rank 3
WITH ranked AS (
    SELECT order_id, channel, amount, customer_id,
           RANK() OVER (PARTITION BY channel ORDER BY amount DESC) AS rk
    FROM   orders
)
SELECT channel, order_id, customer_id, amount, rk
FROM   ranked
WHERE  rk <= 3
ORDER  BY channel, rk;

-- 13. Month-over-month revenue  (pattern 7: Row to row)
-- expected: 42 monthly rows; the first mom_change is NULL, which is correct
WITH monthly AS (
    SELECT   DATE_TRUNC('month', order_date) AS mo,
             SUM(amount)                     AS revenue
    FROM     orders
    GROUP BY 1
)
SELECT mo,
       revenue,
       revenue - LAG(revenue) OVER (ORDER BY mo) AS mom_change,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY mo))
             / NULLIF(LAG(revenue) OVER (ORDER BY mo), 0), 1) AS mom_pct
FROM   monthly
ORDER  BY mo;

-- 14. Cumulative revenue  (pattern 7: Row to row)
-- expected: 42 rows; the final running_total equals total revenue
WITH monthly AS (
    SELECT   DATE_TRUNC('month', order_date) AS mo,
             SUM(amount)                     AS revenue
    FROM     orders
    GROUP BY 1
)
SELECT mo, revenue,
       SUM(revenue) OVER (ORDER BY mo
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM   monthly
ORDER  BY mo;

-- 15. Lapsed customers, done twice  (pattern 8: Boundary date)
-- expected: 9 rows flagged by the naive rule, 4 by the correct one; the 5 false positives are high-spend accounts that last ordered in autumn 2025
WITH per_customer AS (
    SELECT   customer_id,
             MIN(order_date) AS first_order,
             MAX(order_date) AS last_order,
             COUNT(*)        AS n_orders,
             SUM(amount)     AS lifetime_spend
    FROM     orders
    WHERE    customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT customer_id, last_order, n_orders, lifetime_spend,
       CASE WHEN last_order < DATE '2026-01-01' THEN 1 ELSE 0 END AS lapsed_naive,
       CASE WHEN last_order < DATE '2025-07-01' THEN 1 ELSE 0 END AS lapsed_correct
FROM   per_customer
WHERE  last_order < DATE '2026-01-01'
ORDER  BY last_order;

-- 16. Find the customer who came back  (pattern 8: Boundary date)
-- expected: 1 row: a 972-day silence, from a customer most churn queries count as active throughout
WITH gaps AS (
    SELECT customer_id, order_date,
           LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order
    FROM   orders
    WHERE  customer_id IS NOT NULL
)
SELECT customer_id, prev_order, order_date,
       order_date - prev_order AS days_silent
FROM   gaps
WHERE  prev_order IS NOT NULL
  AND  order_date - prev_order > 548
ORDER  BY days_silent DESC;
