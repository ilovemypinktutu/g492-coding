import pandas as pd, duckdb
D="data/"
o=pd.read_csv(D+"orders.csv",parse_dates=["order_date"]); i=pd.read_csv(D+"order_items.csv"); p=pd.read_csv(D+"products.csv")
c=pd.read_csv(D+"customers.csv"); r=pd.read_csv(D+"returns.csv"); fx=pd.read_csv(D+"fx_rates_monthly.csv")
li=i.merge(o,on="order_id").merge(p,on="product_id")
li["month"]=li.order_date.dt.to_period("M").astype(str)
li=li.merge(fx[["month","currency","usd_per_unit"]],on=["month","currency"])
li["net_local"]=li.quantity*li.unit_price*(1-li.discount_pct)
li["net_usd"]=li.net_local*li.usd_per_unit
q2=li[(li.order_date>="2026-04-01")&(li.order_date<"2026-07-01")]
naive=q2.assign(rev=q2.quantity*q2.unit_price).groupby("product_name").rev.sum().nlargest(5)
good=q2[(q2.status=="Completed")&(q2.customer_id<99900)].groupby("product_name").net_usd.sum().nlargest(5)
print("NAIVE top5 (gross, all currencies summed, incl cancelled/test)\n",naive.round(0)); print("CORRECT top5 net USD\n",good.round(0))
print("Q2 naive total",(q2.quantity*q2.unit_price).sum().round(0),"correct total",q2[(q2.status=="Completed")&(q2.customer_id<99900)].net_usd.sum().round(0))
# SQL fan-out
con=duckdb.connect(); [con.register(n,df) for n,df in [("orders",o),("order_items",i),("returns",r),("products",p),("customers",c)]]
print(con.sql("""select sum(oi.quantity*oi.unit_price) gross from order_items oi join orders o using(order_id) where o.currency='USD' and o.status='Completed'""").fetchall())
print(con.sql("""select sum(oi.quantity*oi.unit_price) gross_fanout from order_items oi join orders o using(order_id) left join returns r on r.order_id=oi.order_id and r.product_id=oi.product_id where o.currency='USD' and o.status='Completed'""").fetchall())
print("dup return keys", r.duplicated(["order_id","product_id"]).sum())
print("customers w/o orders", (~c.customer_id.isin(o.customer_id)).sum())
print("missing segment", c.segment.isna().sum())
print("test orders", (o.customer_id>99900).sum(), "cancelled", (o.status=="Cancelled").sum())
