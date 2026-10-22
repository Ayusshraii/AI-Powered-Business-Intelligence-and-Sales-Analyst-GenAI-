"""Makes a fake Superstore-style CSV so you can test the pipeline before downloading the real one."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(1)
n = 3000
cats = {"Furniture": ["Tables", "Chairs"], "Technology": ["Phones", "Copiers"], "Office Supplies": ["Paper", "Binders"]}
rows = []
for i in range(n):
    cat = rng.choice(list(cats))
    sub = rng.choice(cats[cat])
    disc = rng.choice([0, 0, 0.1, 0.2, 0.3, 0.5])
    sales = float(rng.uniform(20, 800))
    profit = sales * (0.25 - disc * 0.9) + rng.normal(0, 10)
    rows.append({
        "Row ID": i + 1, "Order ID": f"CA-{i // 3}", "Order Date": pd.Timestamp("2022-01-01") + pd.Timedelta(days=int(rng.integers(0, 1095))),
        "Ship Mode": rng.choice(["Standard Class", "First Class"]), "Customer ID": f"C{rng.integers(1, 120)}",
        "Customer Name": "Name", "Segment": rng.choice(["Consumer", "Corporate"]), "Region": rng.choice(["West", "East"]),
        "State": "X", "Product ID": f"P-{cat[:3]}-{sub[:3]}-{rng.integers(1, 15)}", "Category": cat, "Sub-Category": sub,
        "Product Name": f"{sub} item", "Sales": sales, "Quantity": int(rng.integers(1, 6)), "Discount": disc, "Profit": profit,
    })
df = pd.DataFrame(rows)
df["Order Date"] = df["Order Date"].dt.strftime("%m/%d/%Y")
df["Ship Date"] = df["Order Date"]
df.to_csv("data/sample.csv", index=False)
print("saved data/sample.csv")
