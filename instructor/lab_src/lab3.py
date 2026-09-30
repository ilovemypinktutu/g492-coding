TITLE = "SQL: Asking the Company's Data"
SLUG = "sql"

CELLS = [
("md", """
**Goal today:** write, read and *check* SQL. In most companies the data lives in a database or a warehouse, and SQL is how you ask it questions.

We use **DuckDB**, a real SQL engine that runs inside this notebook. The SQL you write here works almost unchanged in Snowflake, BigQuery, Postgres or SQL Server.
"""),
("code", """
# %pip install -q duckdb     # uncomment if duckdb is not installed
import duckdb, pandas as pd
con = duckdb.connect()
for t in ["orders", "order_items", "products", "customers", "returns", "fx_rates_monthly"]:
    con.register(t + "_df", pd.read_csv(DATA + t + ".csv"))
    con.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM {t}_df")
    con.unregister(t + "_df")
def q(sql):
    \"\"\"Run a SQL query and show the result as a table.\"\"\"
    return con.sql(sql).df()
q("SHOW TABLES")
"""),
("md", """
## Part 1: The six clauses (10 min)
```sql
SELECT   columns / calculations      -- what to show
FROM     table                       -- where from
JOIN     other ON key                -- look up another table
WHERE    condition                   -- keep some rows (before grouping)
GROUP BY columns                     -- PivotTable rows
HAVING   condition                   -- keep some groups (after grouping)
ORDER BY column DESC LIMIT n         -- sort, top n
```
**1a.** Show the 10 most recent orders from the United Kingdom.
"""),
("code", """
q(\"\"\"
-- your SQL here
\"\"\")
""", """
q(\"\"\"
SELECT order_id, order_date, customer_id, channel, status
FROM orders
WHERE country = 'United Kingdom'
ORDER BY order_date DESC
LIMIT 10
\"\"\")
"""),
("md", "**1b.** For each country: number of orders, number of *completed* orders, and cancellation rate (%). Sort by orders, descending."),
("code", """
q(\"\"\"

\"\"\")
""", """
q(\"\"\"
SELECT country,
       COUNT(*) AS orders,
       SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
       ROUND(100.0 * AVG(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END), 1) AS cancel_rate_pct
FROM orders
GROUP BY country
ORDER BY orders DESC
\"\"\")
"""),
("md", """
## Part 2: Text-to-SQL with AI, then verify (20 min)
Copy the schema printed below into your AI assistant, followed by the question. **Always give the AI the schema**, or it will make up column names.
"""),
("code", """
schema = "\\n".join(
    f"{t}({', '.join(c + ' ' + str(ty) for c, ty in con.sql(f'SELECT * FROM {t} LIMIT 0').df().dtypes.items())})"
    for t in ["orders", "order_items", "products", "customers", "returns", "fx_rates_monthly"])
print(schema)
"""),
("md", """
**2a.** Ask the AI:
> *Using this schema, write one DuckDB SQL query that shows, for each product category, total units sold, total revenue (quantity × unit_price) and total units returned, for completed USD orders.*

Paste and run it. Then run the **grain check** in the next cell before you believe it.
"""),
("code", """
ai_sql = \"\"\"
-- paste the AI's SQL here
\"\"\"
q(ai_sql)
""", """
# The typical AI answer joins returns directly onto order_items:
ai_sql = \"\"\"
SELECT p.category,
       SUM(oi.quantity)                 AS units_sold,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       SUM(r.qty_returned)              AS units_returned
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN returns r ON r.order_id = oi.order_id AND r.product_id = oi.product_id
WHERE o.status = 'Completed' AND o.currency = 'USD'
GROUP BY p.category
ORDER BY revenue DESC
\"\"\"
q(ai_sql)
"""),
("code", """
# Grain check: revenue computed WITHOUT touching returns. Does it match the AI's revenue column?
q(\"\"\"
SELECT p.category, SUM(oi.quantity) AS units_sold, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'Completed' AND o.currency = 'USD'
GROUP BY p.category
ORDER BY revenue DESC
\"\"\")
"""),
("md", """
If the numbers differ, you've found a **join fan-out**: `returns` has more than one row for some (order, product) pairs, so those sales get counted twice. Prove it:
"""),
("code", """
q(\"\"\"
SELECT COUNT(*) AS return_rows,
       COUNT(DISTINCT (order_id, product_id)) AS distinct_lines
FROM returns
\"\"\")
"""),
("md", "**2b.** Fix the query: aggregate `returns` to one row per (order_id, product_id) in a **CTE** (`WITH r AS (...)`) *before* joining. Your revenue must match the grain check exactly."),
("code", """
q(\"\"\"

\"\"\")
""", """
q(\"\"\"
WITH r AS (
    SELECT order_id, product_id, SUM(qty_returned) AS qty_returned
    FROM returns
    GROUP BY order_id, product_id
)
SELECT p.category,
       SUM(oi.quantity)                 AS units_sold,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       SUM(r.qty_returned)              AS units_returned,
       ROUND(100.0 * SUM(r.qty_returned) / SUM(oi.quantity), 1) AS return_rate_pct
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN r     ON r.order_id = oi.order_id AND r.product_id = oi.product_id
WHERE o.status = 'Completed' AND o.currency = 'USD'
GROUP BY p.category
ORDER BY revenue DESC
\"\"\")
"""),
("md", """
## Part 3: INNER vs LEFT JOIN (10 min)
Marketing asks: *"How many orders does the average customer place?"*

**3a.** Predict: will these two queries give the same answer? Then run them.
"""),
("code", """
inner = q(\"\"\"
SELECT AVG(n) AS avg_orders FROM (
    SELECT c.customer_id, COUNT(o.order_id) AS n
    FROM customers c JOIN orders o ON o.customer_id = c.customer_id
    WHERE NOT c.is_test
    GROUP BY c.customer_id)
\"\"\")
left = q(\"\"\"
SELECT AVG(n) AS avg_orders FROM (
    SELECT c.customer_id, COUNT(o.order_id) AS n
    FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id
    WHERE NOT c.is_test
    GROUP BY c.customer_id)
\"\"\")
print("INNER:", inner.avg_orders[0].round(2), "  LEFT:", left.avg_orders[0].round(2))
"""),
("md", """
**3b.** In one sentence each: which customers does each query include? Which one answers Marketing's question? (It depends on the question they *meant*, so write the clarifying question you'd send back.)

## Part 4: Window functions, the "top N per group" pattern (10 min)
**4a.** Ask the AI for: *the single best-selling product (by units, completed orders) in each country*. It should use `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`. Run it and check that you get exactly one row per country.
"""),
("code", """
q(\"\"\"

\"\"\")
""", """
q(\"\"\"
WITH units AS (
    SELECT o.country, p.product_name, SUM(oi.quantity) AS units
    FROM order_items oi
    JOIN orders o   ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.status = 'Completed' AND NOT c.is_test
    GROUP BY o.country, p.product_name
)
SELECT country, product_name, units
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY country ORDER BY units DESC) AS rk FROM units)
WHERE rk = 1
ORDER BY units DESC
\"\"\")
"""),
("md", """
### Exit ticket (submit)
Write the **three checks** you will run on any AI-written SQL query before you send its numbers to anyone. (Hint: row counts, a total you can reproduce another way, and ___.)
"""),
]
