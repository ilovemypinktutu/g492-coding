"""Generate the synthetic 'Limestone Outfitters' dataset used in Labs 1-3 and 5.
Reproducible: seed 492. FX rates are real ECB monthly averages via frankfurter.dev."""
import numpy as np, pandas as pd, requests, os
rng = np.random.default_rng(492)
OUT = os.path.join(os.path.dirname(__file__), "..", "data")

# ---- products ----
cats = {
 "Tents": [("Ridgeline 2P Tent", 289), ("Ridgeline 4P Tent", 419), ("Featherlite 1P Tent", 349), ("Basecamp 6P Tent", 529), ("Trail Tarp Shelter", 119)],
 "Backpacks": [("Daytripper 22L Pack", 89), ("Summit 45L Pack", 199), ("Expedition 65L Pack", 279), ("Commuter 18L Pack", 69), ("Hydration Vest 8L", 99), ("Kids Explorer Pack", 49)],
 "Footwear": [("Canyon Hiking Boot", 179), ("Canyon Hiking Boot WP", 209), ("Trailrunner Shoe", 139), ("Camp Slide", 39), ("Approach Shoe", 159), ("Winter Pac Boot", 189)],
 "Apparel": [("Merino Base Layer Top", 89), ("Merino Base Layer Bottom", 79), ("Storm Shell Jacket", 249), ("Down Puffy Jacket", 229), ("Fleece Quarter-Zip", 79), ("Trail Pant", 85), ("Sun Hoodie", 59), ("Wool Hiking Sock 3-Pack", 32)],
 "Camp Kitchen": [("Titanium Pot Set", 79), ("Canister Stove", 59), ("Insulated Mug", 29), ("Water Filter Squeeze", 45), ("Camp Utensil Kit", 19), ("Collapsible Sink 10L", 25)],
 "Accessories": [("LED Headlamp 400", 49), ("Trekking Poles (pair)", 119), ("Sleeping Bag 20F", 239), ("Sleeping Pad Insulated", 149), ("Dry Bag 20L", 29), ("First Aid Kit", 35), ("Camp Chair", 99)],
}
rows = []
pid = 101
for c, items in cats.items():
    for name, price in items:
        rows.append(dict(product_id=pid, product_name=name, category=c, list_price_usd=float(price),
                         unit_cost_usd=round(price * rng.uniform(0.38, 0.55), 2)))
        pid += 1
products = pd.DataFrame(rows)

# ---- fx (real, monthly average, units of local currency per 1 USD) ----
r = requests.get("https://api.frankfurter.dev/v1/2025-01-01..2026-06-30", params={"base": "USD", "symbols": "EUR,GBP"}, timeout=30).json()
fx = pd.DataFrame(r["rates"]).T.rename_axis("date").reset_index()
fx["month"] = pd.to_datetime(fx["date"]).dt.to_period("M").astype(str)
fxm = fx.groupby("month")[["EUR", "GBP"]].mean().reset_index()
fx_long = fxm.melt(id_vars="month", var_name="currency", value_name="per_usd")
fx_long = pd.concat([fx_long, pd.DataFrame({"month": fxm.month, "currency": "USD", "per_usd": 1.0})])
fx_long["usd_per_unit"] = 1 / fx_long["per_usd"]
fx_long = fx_long.sort_values(["month", "currency"]).round(6)

# local price lists (set once, psychologically rounded) -> prices differ by market
price_mult = {"USD": 1.0, "EUR": 0.95, "GBP": 0.82}
def local_price(usd, cur): return float(np.floor(usd * price_mult[cur]) - 0.01) if cur != "USD" else usd - 0.01

# ---- customers ----
countries = ["United States", "United Kingdom", "Germany", "France", "Ireland", "Netherlands"]
cprob = [0.58, 0.16, 0.11, 0.07, 0.04, 0.04]
cur_of = {"United States": "USD", "United Kingdom": "GBP"}
N = 3200
cust = pd.DataFrame({
    "customer_id": np.arange(10001, 10001 + N),
    "signup_date": pd.to_datetime("2023-06-01") + pd.to_timedelta(rng.integers(0, 1096, N), "D"),
    "country": rng.choice(countries, N, p=cprob),
    "segment": rng.choice(["Consumer", "Business"], N, p=[0.86, 0.14]).astype(object),
    "acquisition_channel": rng.choice(["Organic search", "Paid social", "Referral", "Email", "Marketplace"], N, p=[.34, .26, .14, .14, .12]),
    "is_test": False,
})
cust.loc[rng.choice(N, 96, replace=False), "segment"] = None          # missing segment (CRM gap)
test = pd.DataFrame({"customer_id": [99901, 99902, 99903], "signup_date": pd.to_datetime(["2024-01-02"] * 3),
                     "country": ["United States", "United Kingdom", "Germany"], "segment": ["Business"] * 3,
                     "acquisition_channel": ["Internal"] * 3, "is_test": True})
cust = pd.concat([cust, test], ignore_index=True)

# ---- orders ----
days = pd.date_range("2025-01-01", "2026-06-30")
season = {1: .75, 2: .8, 3: 1.0, 4: 1.15, 5: 1.3, 6: 1.3, 7: 1.2, 8: 1.1, 9: 1.0, 10: .95, 11: 1.25, 12: 1.45}
weights = np.array([season[d.month] * (1 + 0.22 * (d - days[0]).days / 365) * (1.12 if d.dayofweek >= 5 else 1) for d in days])
n_orders = 26000
odates = rng.choice(days, n_orders, p=weights / weights.sum())
real = cust[~cust.is_test]
buyer_w = rng.pareto(1.6, len(real)) + 0.2
ocust = rng.choice(real.customer_id.values, n_orders, p=buyer_w / buyer_w.sum())
orders = pd.DataFrame({"order_date": pd.to_datetime(odates), "customer_id": ocust})
orders = orders.merge(cust[["customer_id", "signup_date", "country"]], on="customer_id")
orders = orders[orders.order_date >= orders.signup_date].drop(columns="signup_date")
# test orders
t = pd.DataFrame({"order_date": pd.to_datetime(rng.choice(days, 14)), "customer_id": rng.choice([99901, 99902, 99903], 14)})
t = t.merge(cust[["customer_id", "country"]], on="customer_id")
orders = pd.concat([orders, t]).sort_values("order_date").reset_index(drop=True)
orders.insert(0, "order_id", np.arange(500001, 500001 + len(orders)))
orders["currency"] = orders.country.map(lambda c: cur_of.get(c, "EUR"))
orders["channel"] = rng.choice(["Web", "Mobile app", "Marketplace"], len(orders), p=[.55, .33, .12])
orders["status"] = rng.choice(["Completed", "Cancelled"], len(orders), p=[.955, .045])

# ---- order items ----
cat_pop = {"Tents": .09, "Backpacks": .15, "Footwear": .19, "Apparel": .32, "Camp Kitchen": .12, "Accessories": .13}
pw = products.category.map(cat_pop) / products.groupby("category").product_id.transform("count")
pw = pw / pw.sum()
items = []
for o in orders.itertuples():
    istest = o.customer_id > 99900
    k = rng.choice([1, 2, 3, 4, 5], p=[.52, .27, .12, .06, .03])
    prods = rng.choice(products.product_id.values, k, replace=False, p=pw.values)
    disc_rate = rng.choice([0, .1, .2, .3], p=[.72, .15, .1, .03])
    if o.order_date.month in (11, 12) and rng.random() < .35: disc_rate = max(disc_rate, .2)
    for ln, p in enumerate(prods, 1):
        lp = products.loc[products.product_id == p, "list_price_usd"].iat[0]
        q = int(rng.integers(40, 250)) if istest else int(rng.choice([1, 1, 1, 1, 2, 2, 3]))
        items.append((o.order_id, ln, int(p), q, local_price(lp, o.currency), disc_rate))
items = pd.DataFrame(items, columns=["order_id", "line_no", "product_id", "quantity", "unit_price", "discount_pct"])

# ---- returns (some lines returned in 2 separate events -> multiple rows per order+product) ----
comp = items.merge(orders[["order_id", "order_date", "status", "customer_id"]], on="order_id")
comp = comp[(comp.status == "Completed") & (comp.customer_id < 99900)]
comp = comp.merge(products[["product_id", "category"]], on="product_id")
rrate = comp.category.map({"Footwear": .14, "Apparel": .10, "Tents": .05, "Backpacks": .05, "Camp Kitchen": .03, "Accessories": .04})
ret = comp[rng.random(len(comp)) < rrate].copy()
reasons = {"Footwear": ["Wrong size", "Wrong size", "Uncomfortable", "Defective"], "Apparel": ["Wrong size", "Wrong size", "Not as described", "Changed mind"]}
rows = []
for x in ret.itertuples():
    rs = reasons.get(x.category, ["Defective", "Changed mind", "Not as described", "Arrived damaged"])
    if x.quantity >= 2 and rng.random() < .45:   # partial returns in two events
        rows.append((x.order_id, x.product_id, x.order_date + pd.Timedelta(days=int(rng.integers(5, 20))), 1, rng.choice(rs)))
        rows.append((x.order_id, x.product_id, x.order_date + pd.Timedelta(days=int(rng.integers(21, 45))), int(rng.integers(1, x.quantity)), rng.choice(rs)))
    else:
        rows.append((x.order_id, x.product_id, x.order_date + pd.Timedelta(days=int(rng.integers(5, 30))), x.quantity, rng.choice(rs)))
returns = pd.DataFrame(rows, columns=["order_id", "product_id", "return_date", "qty_returned", "reason"]).sort_values("return_date")
returns.insert(0, "return_id", np.arange(1, len(returns) + 1))

cust["signup_date"] = cust.signup_date.dt.date
orders["order_date"] = orders.order_date.dt.date
returns["return_date"] = returns.return_date.dt.date
for name, df in [("products", products), ("customers", cust), ("orders", orders), ("order_items", items), ("returns", returns), ("fx_rates_monthly", fx_long)]:
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
    print(f"{name:18s} {df.shape}")
