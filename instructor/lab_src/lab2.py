TITLE = "Reading Python You Didn't Write"
SLUG = "reading_code"

CELLS = [
("md", """
**Goal today:** get fast at *reading* pandas code, because AI will write most of it for you.

Every exercise follows the same loop:
1. **Predict**: read the code and write down what you expect *before* running it (a number, a shape, "error").
2. **Run** it.
3. **Explain**: if you were wrong, find out why. Asking the AI "explain this line by line" is allowed *after* you predict.

Five snippets below were "written by an AI". **Four of them contain a bug, and only one of those bugs crashes.**
"""),
("code", """
import pandas as pd
orders = pd.read_csv(DATA + "orders.csv")            # note: no parse_dates
items = pd.read_csv(DATA + "order_items.csv")
products = pd.read_csv(DATA + "products.csv")
customers = pd.read_csv(DATA + "customers.csv")
returns = pd.read_csv(DATA + "returns.csv")
print(len(orders), len(items), len(customers), len(returns))
"""),
("md", """
## Warm-up: the 8 verbs (Excel → pandas)

| You want to… | Excel | pandas |
|---|---|---|
| keep some rows | Filter | `df[df.col == x]` |
| keep some columns | hide columns | `df[["a", "b"]]` |
| add a calculated column | new formula column | `df["c"] = df.a * df.b` |
| summarize by group | PivotTable | `df.groupby("g").col.sum()` |
| look up from another table | XLOOKUP | `df.merge(other, on="key")` |
| sort | Sort | `df.sort_values("col")` |
| count rows | COUNTA | `len(df)`, `df.shape` |
| save | Save As | `df.to_csv(...)`, `df.to_excel(...)` |
"""),
("md", """
## Snippet A: a working example (predict the shape)
```python
a = (orders[orders.status == "Completed"]
       .groupby(["country", "channel"])
       .order_id.count()
       .unstack())
```
**Predict:** how many rows and columns will `a` have? What does each cell mean?
"""),
("code", """
prediction_A = ""   # e.g. "6 rows (countries) x 3 columns (channels); cells = # completed orders"
a = (orders[orders.status == "Completed"].groupby(["country", "channel"]).order_id.count().unstack())
a
"""),
("md", """
## Snippet B: "US orders from the website"
```python
web_us = orders[orders.country == "United States" & orders.channel == "Web"]
```
**Predict:** how many rows? (Or will it fail?)
"""),
("code", """
prediction_B = ""
web_us = orders[orders.country == "United States" & orders.channel == "Web"]
""", """
prediction_B = "error"
try:
    web_us = orders[orders.country == "United States" & orders.channel == "Web"]
except Exception as e:
    print(type(e).__name__, "-", str(e)[:120])
# Fix: & binds tighter than ==, so each condition needs parentheses.
web_us = orders[(orders.country == "United States") & (orders.channel == "Web")]
print("fixed:", len(web_us), "rows")
"""),
("md", """
This was the **loud** bug: it crashed, so you couldn't miss it. The rest are **silent**. They run, and they give you a number that looks fine.

## Snippet C: "Q2 2026 orders"
```python
q2 = orders[(orders.order_date >= "2026-4-1") & (orders.order_date <= "2026-6-30")]
```
**Predict:** roughly how many orders were placed in Q2 2026? (Hint: about 20,700 orders over 18 months, and Q2 is a busy season.)
"""),
("code", """
prediction_C = ""
q2 = orders[(orders.order_date >= "2026-4-1") & (orders.order_date <= "2026-6-30")]
len(q2)
""", """
prediction_C = "~4,500"
q2 = orders[(orders.order_date >= "2026-4-1") & (orders.order_date <= "2026-6-30")]
print("buggy:", len(q2))
# order_date was read as TEXT, so this compares strings character by character.
# "2026-04-15" < "2026-4-1" because '0' < '4', so every April-June date fails the first test.
orders["order_date"] = pd.to_datetime(orders.order_date)
q2 = orders[(orders.order_date >= "2026-04-01") & (orders.order_date <= "2026-06-30")]
print("fixed:", len(q2))
"""),
("md", """
**Explain in one sentence** why the result was wrong. (Try `orders.dtypes` and `"2026-05-10" >= "2026-4-1"`.)

## Snippet D: "Revenue and returns by product"
```python
lines = items.merge(returns, on=["order_id", "product_id"], how="left")
lines["revenue"] = lines.quantity * lines.unit_price
print(len(items), len(lines))
```
**Predict:** will `len(lines)` equal `len(items)`? (A left join keeps every row on the left… right?)
"""),
("code", """
prediction_D = ""
lines = items.merge(returns, on=["order_id", "product_id"], how="left")
lines["revenue"] = lines.quantity * lines.unit_price
print(len(items), len(lines))
""", """
prediction_D = "same number of rows"
lines = items.merge(returns, on=["order_id", "product_id"], how="left")
lines["revenue"] = lines.quantity * lines.unit_price
print("items:", len(items), " after merge:", len(lines), " extra rows:", len(lines) - len(items))
print("revenue inflated by:", f"{lines.revenue.sum() / (items.quantity * items.unit_price).sum() - 1:.2%}")
# A left join keeps every left row AT LEAST once. A line returned in two events matches 2 return rows,
# so it appears twice and its revenue is double counted.
# Fix: aggregate returns to the grain of items FIRST, then merge.
r = returns.groupby(["order_id", "product_id"], as_index=False).qty_returned.sum()
fixed = items.merge(r, on=["order_id", "product_id"], how="left", validate="one_to_one")
print("fixed rows:", len(fixed))
"""),
("md", """
**Habit to steal:** `merge(..., validate="one_to_one")` or `"many_to_one"` makes pandas *crash* instead of silently duplicating rows. Turn silent bugs into loud ones.

## Snippet E: "Revenue by customer segment"
```python
seg = (orders.merge(items, on="order_id").merge(customers, on="customer_id")
         .assign(rev=lambda d: d.quantity * d.unit_price)
         .groupby("segment").rev.sum())
print(seg, seg.sum())
```
**Predict:** will `seg.sum()` equal the total of `quantity * unit_price` over all items?
"""),
("code", """
prediction_E = ""
seg = (orders.merge(items, on="order_id").merge(customers, on="customer_id")
         .assign(rev=lambda d: d.quantity * d.unit_price).groupby("segment").rev.sum())
print(seg, "\\nsum of segments:", round(seg.sum()), " total:", round((items.quantity * items.unit_price).sum()))
""", """
prediction_E = "yes"
seg = (orders.merge(items, on="order_id").merge(customers, on="customer_id")
         .assign(rev=lambda d: d.quantity * d.unit_price).groupby("segment").rev.sum())
total = (items.quantity * items.unit_price).sum()
print(seg, "\\nsum of segments:", round(seg.sum()), " total:", round(total), " missing:", round(total - seg.sum()))
# groupby drops rows whose key is NaN by default: 96 customers have no segment.
print(orders.merge(items, on="order_id").merge(customers, on="customer_id")
        .assign(rev=lambda d: d.quantity * d.unit_price).groupby("segment", dropna=False).rev.sum())
"""),
("md", """
## Snippet F: "What's our average discount?"
```python
avg_disc = items.groupby("order_id").discount_pct.mean().mean()
```
**Predict:** is this the average discount *per dollar sold*? Per order? Per line? Which one would Finance want?
"""),
("code", """
prediction_F = ""
avg_disc = items.groupby("order_id").discount_pct.mean().mean()
avg_disc
""", """
prediction_F = "per order, not per dollar"
per_order = items.groupby("order_id").discount_pct.mean().mean()
per_line = items.discount_pct.mean()
gross = items.quantity * items.unit_price
per_dollar = (gross * items.discount_pct).sum() / gross.sum()
print(f"per order {per_order:.3%} | per line {per_line:.3%} | per dollar (weighted) {per_dollar:.3%}")
# Not a code bug: an unstated definition. All three are 'correct' code; only the spec decides.
"""),
("md", """
## Part 2: Your turn to be the reviewer (15 min)
Ask your AI assistant:
> *Using orders.csv, order_items.csv and customers.csv, compute each acquisition channel's average net revenue per customer for customers who signed up in 2025.*

Then **before running**, annotate every line of its code with a comment in your own words, and mark each line where it made an assumption (e.g., which customers count, what "net" means, currency, customers with zero orders).
Run it, then write the two assumptions most likely to change the answer.
"""),
("code", """
# Paste AI code here, with YOUR comment on every line

""", """
# Assumptions that matter: customers with zero orders (include as 0?), cancelled/test orders,
# currency conversion, discount. A left join from customers keeps zero-order customers.
c25 = customers[(pd.to_datetime(customers.signup_date).dt.year == 2025) & (~customers.is_test)]
rev = (orders[orders.status == "Completed"].merge(items, on="order_id")
          .assign(net=lambda d: d.quantity * d.unit_price * (1 - d.discount_pct))
          .groupby("customer_id").net.sum())
c25 = c25.assign(net=c25.customer_id.map(rev).fillna(0))
print(c25.groupby("acquisition_channel").net.agg(["mean", "count"]).round(1))
print("\\nIf zero-order customers are dropped instead:")
print(c25[c25.net > 0].groupby("acquisition_channel").net.mean().round(1))
"""),
("md", """
### Exit ticket (submit)
1. Which snippet's bug would have been **most dangerous** in a real report? Why?
2. Write one habit you'll use every time AI gives you pandas code.
"""),
]
