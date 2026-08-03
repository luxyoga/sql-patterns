# Exercises

Sixteen problems, two per pattern, in the order the patterns appear in the post.

Treat **2026-07-01** as today. The data deliberately ends on 2026-06-30, so every
answer here is stable forever. Nothing uses `CURRENT_DATE`, which means these
numbers will not drift out from under you next month.

Work top to bottom. Before writing any SQL, say out loud which of the eight patterns
the question is. If you can name it, the query is mostly filling in blanks.

Each problem lists a self-check so you can confirm you got it without reading the
solution. Solutions are in `solutions/SOLUTIONS.sql`.

### 1. The five largest orders
*Pattern 1 — Filter and sort*

Return the five highest-value orders: order id, customer id, amount.

> **Hint.** No 'per' and no 'each' in the question. That rules out GROUP BY and window functions.

> **Self-check.** 5 rows; top amount is 2100.00

### 2. Most recent signups in Copenhagen
*Pattern 1 — Filter and sort*

The three customers in Copenhagen who signed up most recently.

> **Hint.** Same shape as above with a WHERE clause bolted on.

> **Self-check.** 3 rows

### 3. Revenue by channel
*Pattern 2 — Group and aggregate*

For each channel: total revenue, order count, and average order value. Only channels with at least 50 orders. Highest revenue first.

> **Hint.** 'For each' names the GROUP BY column. 'At least 50 orders' mentions an aggregate, so it is HAVING, not WHERE.

> **Self-check.** 4 rows

### 4. Heavy buyers
*Pattern 2 — Group and aggregate*

Customers who have placed 10 or more orders. Return customer id, order count, and lifetime spend, most orders first.

> **Hint.** The filter is on a count, so it belongs in HAVING. Exclude the guest-checkout row with a WHERE.

> **Self-check.** 22 rows

### 5. Put names on the biggest orders
*Pattern 3 — Join to enrich*

The ten largest orders, showing the customer's name and city alongside the amount.

> **Hint.** The question asks for a column that does not exist on orders. That is the join signal. Watch what happens to the guest-checkout order under INNER vs LEFT.

> **Self-check.** 10 rows

### 6. Revenue by city
*Pattern 3 — Join to enrich*

Total revenue and customer count per city, biggest first. Two customers have no city on file: make sure they are visible rather than silently dropped.

> **Hint.** COALESCE the city before grouping, otherwise NULL becomes an unlabelled bucket in the output.

> **Self-check.** 9 rows, including an '(unknown)' bucket

### 7. Customers who have never ordered
*Pattern 4 — Anti-join (the absence pattern)*

List every customer with no orders at all.

> **Hint.** 'Never' means NOT EXISTS. Try it with NOT IN too, then work out why that version returns nothing.

> **Self-check.** 6 rows -- and the NOT IN version returns 0, which is the point

### 8. Ordered in 2025, gone in 2026
*Pattern 4 — Anti-join (the absence pattern)*

Customers who placed at least one order during 2025 but none in 2026.

> **Hint.** Two conditions: one EXISTS, one NOT EXISTS, against the same table with different date filters.

> **Self-check.** 7 rows

### 9. Large-order share by channel
*Pattern 5 — Conditional aggregation*

Per channel, in one row each: total orders, how many were 1000 or more, and that as a percentage of the channel's orders.

> **Hint.** CASE inside the aggregate. Guard the division with NULLIF so an empty channel cannot blow up.

> **Self-check.** 4 rows

### 10. Bucket customers by lifetime value
*Pattern 5 — Conditional aggregation*

Classify each customer as Major (5000+), Mid (1500-4999) or Standard, and count how many fall in each tier.

> **Hint.** Aggregate to one row per customer first, then CASE over that. Order the thresholds from highest down, since CASE stops at the first match.

> **Self-check.** 3 tiers

### 11. Each customer's largest order
*Pattern 6 — Top N per group*

For every customer, the single largest order they have placed, with its date. One row per customer.

> **Hint.** Rank inside a CTE, filter on the rank outside it. You cannot filter on the window column in the same SELECT that creates it. One customer has two orders tied at their maximum: decide whether ROW_NUMBER or RANK is correct here.

> **Self-check.** 34 rows with ROW_NUMBER, 35 with RANK -- the extra row is the tie

### 12. Top three orders per channel
*Pattern 6 — Top N per group*

The three largest orders within each channel. Run it with ROW_NUMBER and again with RANK and explain the row-count difference.

> **Hint.** One channel has two orders tied for third place.

> **Self-check.** 13 rows with RANK, 12 with ROW_NUMBER -- 'partner' has a tie at rank 3

### 13. Month-over-month revenue
*Pattern 7 — Row to row*

Monthly revenue with the change versus the previous month, in absolute terms and as a percentage.

> **Hint.** Aggregate to the month first, then window over that result. Doing both in one pass is how you tie yourself in knots.

> **Self-check.** 42 monthly rows; the first mom_change is NULL, which is correct

### 14. Cumulative revenue
*Pattern 7 — Row to row*

Running total of revenue by month across the whole dataset.

> **Hint.** SUM() OVER with an explicit frame. Leaving the frame out gives you RANGE semantics, which behaves differently when the ORDER BY column has duplicates.

> **Self-check.** 42 rows; the final running_total equals total revenue

### 15. Lapsed customers, done twice
*Pattern 8 — Boundary date*

Treat 2026-07-01 as today. Write the naive version first: customers with no order in calendar 2026. Then write the correct version: customers whose most recent order is more than twelve months old. Compare the counts and look at who the difference is.

> **Hint.** Collapse to one row per customer with MIN and MAX of order_date, then ask your question of that. Both queries run clean. Only one is right.

> **Self-check.** 9 rows flagged by the naive rule, 4 by the correct one; the 5 false positives are high-spend accounts that last ordered in autumn 2025

### 16. Find the customer who came back
*Pattern 8 — Boundary date*

Find reactivations: a customer who went silent for more than eighteen months and then ordered again. Run it at a twelve-month threshold first and see how much noise you get, then move to eighteen.

> **Hint.** This is pattern 7 doing pattern 8's job: LAG within customer, then filter on the gap. At 365 days you get 12 rows, most of them just sparse buyers. At 548 you get the one account that actually tells a story.

> **Self-check.** 1 row: a 972-day silence, from a customer most churn queries count as active throughout
