TITLE = "From Spec to Code"
SLUG = "spec_to_code"

DICTIONARY = """
### Data dictionary: Limestone Outfitters (fictional outdoor-gear retailer, Jan 2025 – Jun 2026)

| Table | One row is… | Key columns |
|---|---|---|
| `orders` | one order | `order_id`, `customer_id`, `order_date`, `country`, **`currency`** (USD, GBP or EUR), `channel`, **`status`** (Completed / Cancelled) |
| `order_items` | one product line within an order | `order_id`, `line_no`, `product_id`, `quantity`, **`unit_price` (in the order's local currency)**, **`discount_pct`** (0.2 = 20% off) |
| `products` | one product | `product_id`, `product_name`, `category`, `list_price_usd`, `unit_cost_usd` |
| `customers` | one customer account | `customer_id`, `signup_date`, `country`, `segment` (may be blank), `acquisition_channel`, **`is_test`** (internal QA accounts) |
| `returns` | one return *event* (a line can be returned in more than one event) | `return_id`, `order_id`, `product_id`, `return_date`, `qty_returned`, `reason` |
| `fx_rates_monthly` | one currency in one month | `month` (YYYY-MM), `currency`, `per_usd`, **`usd_per_unit`** (multiply local amount by this to get USD). Real ECB monthly averages. |

**Company definitions (from Finance):**
- *Net revenue* = quantity × unit_price × (1 − discount_pct), converted to USD at the order month's average rate.
- Revenue counts **Completed** orders only, and **never** includes test accounts.
"""

CELLS = [
("md", """
**Goal today:** see for yourself that the quality of AI-written code depends on the quality of your *specification*.

You will answer one business question twice:
1. **Round 1**: with a one-sentence prompt, the way most people use AI.
2. **Round 2**: with a written spec.

Then you'll compare the answers and explain the difference.

⏱ ~40 minutes. Work in pairs: one person *drives* (types), the other *navigates* (reads and questions every line).
"""),
("md", "## Part 1: Meet the data (5 min)\nRun the cell. For each table, write down **what one row represents** (its *grain*). This is the single most useful habit in analytics."),
("code", """
import pandas as pd
tables = ["orders", "order_items", "products", "customers", "returns", "fx_rates_monthly"]
df = {t: pd.read_csv(DATA + t + ".csv") for t in tables}
for t in tables:
    print(f"{t:18s} {df[t].shape[0]:>7,} rows  columns: {list(df[t].columns)}")
"""),
("code", "df['order_items'].head()"),
("md", """
## Part 2, Round 1: the one-line prompt (10 min)
Open your AI assistant (Gemini in Colab, ChatGPT, Claude or Copilot) and type **exactly** this, nothing more:

> *I have CSV files orders.csv, order_items.csv and products.csv. Write pandas code to find the top 5 products by revenue in Q2 2026. The data is in a variable `DATA` that holds the folder path.*

Paste the code it gives you into the cell below and run it. If it errors, paste the error back to the AI **once**. Record the answer.
"""),
("code", """
# Round 1: paste the AI's code here

""", """
# INSTRUCTOR: a typical Round-1 answer. It sums quantity * unit_price across currencies,
# ignores discounts, includes cancelled orders AND test accounts.
orders = pd.read_csv(DATA + "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(DATA + "order_items.csv")
products = pd.read_csv(DATA + "products.csv")
q2 = orders[(orders.order_date >= "2026-04-01") & (orders.order_date <= "2026-06-30")]
m = q2.merge(items, on="order_id").merge(products, on="product_id")
m["revenue"] = m.quantity * m.unit_price
round1 = m.groupby("product_name").revenue.sum().nlargest(5)
round1
"""),
("code", """
# Record your Round 1 top-5 (product names, in order) and total Q2 revenue it implies
round1_top5 = []
round1_total = None
""", """
round1_top5 = list(round1.index)
round1_total = m.revenue.sum()
round1_top5, round(round1_total)
"""),
("md", "## Part 3: Read the data dictionary (5 min)\n" + DICTIONARY + """
**Discuss with your partner:** list every way your Round 1 code could be wrong *given this dictionary*. Aim for at least four.
"""),
("md", """
## Part 4, Round 2: write a spec, then prompt (15 min)
Fill in the template below **before** you touch the AI. Then paste the whole spec as your prompt.

```
GOAL:        What decision will this answer support?
INPUTS:      Which files/tables, and what is one row of each?
DEFINITIONS: Precisely define every business term (revenue, Q2 2026, product...)
FILTERS:     What must be excluded, and why?
OUTPUT:      Exact shape: columns, units, sort order, rounding.
CHECKS:      What should the code print so a human can verify it?
             (row counts before/after each join, totals, anything suspicious)
```
"""),
("code", """
spec = \"\"\"
GOAL:
INPUTS:
DEFINITIONS:
FILTERS:
OUTPUT:
CHECKS:
\"\"\"
""", """
spec = \"\"\"
GOAL: Rank products by Q2 2026 net revenue for the merchandising review.
INPUTS: orders (1 row/order), order_items (1 row/order line), products (1 row/product),
        customers (1 row/customer, has is_test), fx_rates_monthly (1 row/month x currency).
DEFINITIONS: Q2 2026 = order_date from 2026-04-01 to 2026-06-30 inclusive.
        Net revenue = quantity * unit_price * (1 - discount_pct), converted to USD
        with usd_per_unit for the order's month and currency.
FILTERS: status == 'Completed'; exclude customers where is_test is True.
OUTPUT: top 5 products: product_name, category, net_revenue_usd (rounded to $), sorted desc.
CHECKS: print row counts after each merge (must not grow unexpectedly),
        number of test/cancelled lines removed, and total Q2 net revenue.
\"\"\"
"""),
("code", """
# Round 2: paste the AI's code here

""", """
orders = pd.read_csv(DATA + "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(DATA + "order_items.csv")
products = pd.read_csv(DATA + "products.csv")
customers = pd.read_csv(DATA + "customers.csv")
fx = pd.read_csv(DATA + "fx_rates_monthly.csv")

q2 = orders[(orders.order_date >= "2026-04-01") & (orders.order_date <= "2026-06-30")]
print("Q2 orders:", len(q2))
q2 = q2.merge(customers[["customer_id", "is_test"]], on="customer_id", how="left")
print("after customer merge:", len(q2), "| test orders:", q2.is_test.sum(), "| cancelled:", (q2.status == "Cancelled").sum())
q2 = q2[(q2.status == "Completed") & (~q2.is_test)]
lines = q2.merge(items, on="order_id")
print("order lines:", len(lines))
lines["month"] = lines.order_date.dt.strftime("%Y-%m")
lines = lines.merge(fx[["month", "currency", "usd_per_unit"]], on=["month", "currency"], how="left")
assert lines.usd_per_unit.notna().all(), "missing FX rate"
lines["net_revenue_usd"] = lines.quantity * lines.unit_price * (1 - lines.discount_pct) * lines.usd_per_unit
lines = lines.merge(products[["product_id", "product_name", "category"]], on="product_id")
print("lines after product merge:", len(lines))
round2 = (lines.groupby(["product_name", "category"]).net_revenue_usd.sum()
               .nlargest(5).round(0).reset_index())
print("Total Q2 net revenue (USD):", round(lines.net_revenue_usd.sum()))
round2
"""),
("md", """
## Part 5: Compare and explain (5 min)
1. Did the ranking change? Did the total change? By how much (%)?
2. Which **line of your spec** caused each difference? Name it.
3. Round 1 ran without errors. How would your manager ever have known it was wrong?

Write 3–5 sentences in the cell below. **This is what you submit** (plus both code cells).
"""),
("code", """
reflection = \"\"\"

\"\"\"
""", """
round2_total = lines.net_revenue_usd.sum()
print("Round 1 total:", round(round1_total), " Round 2 total:", round(round2_total),
      f" overstatement: {round1_total / round2_total - 1:.1%}")
print("Round 1 top5:", round1_top5)
print("Round 2 top5:", list(round2.product_name))
# Talking points: #4 and #5 change (test accounts buy huge quantities of footwear);
# summing GBP/EUR/USD as if equal; discounts ignored; cancelled orders counted.
"""),
("md", """
### Homework (before Lecture 2)
Find **five** entry-level analyst job postings (LinkedIn, Handshake, company sites). Tally every technical skill mentioned in a shared class sheet (SQL, Python, Excel, Tableau/Power BI, AI tools, statistics...). We'll use the tally at the start of next class.
"""),
]
