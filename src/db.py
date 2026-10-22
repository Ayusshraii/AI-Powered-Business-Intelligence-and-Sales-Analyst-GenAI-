"""Cleans the Superstore CSV and builds the SQLite database."""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sales.db"


def clean(csv_path):
    df = pd.read_csv(csv_path, encoding="latin-1")
    df.columns = [c.strip().lower().replace("-", "_").replace(" ", "_") for c in df.columns]
    n0 = len(df)

    df = df.drop_duplicates()
    df = df.dropna(subset=["order_id", "order_date", "product_id", "customer_id"])
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed")
    for col in ["sales", "profit", "discount", "quantity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["sales", "profit", "discount", "quantity"])
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    print(f"rows before: {n0}, after cleaning: {len(df)}")
    return df


def build_db(csv_path):
    df = clean(csv_path)
    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)
    # split the flat file into 4 tables so we can practise joins
    customers = df[["customer_id", "customer_name", "segment", "region", "state"]].drop_duplicates("customer_id")
    products = df[["product_id", "product_name", "category", "sub_category"]].drop_duplicates("product_id")
    orders = df[["order_id", "order_date", "ship_mode", "customer_id"]].drop_duplicates("order_id")
    items = df[["order_id", "product_id", "sales", "quantity", "discount", "profit"]].reset_index(drop=True)
    items.insert(0, "item_id", items.index + 1)

    customers.to_sql("customers", con, index=False)
    products.to_sql("products", con, index=False)
    orders.to_sql("orders", con, index=False)
    items.to_sql("order_items", con, index=False)

    # one view with everything joined, the agent only talks to this
    con.execute("""
        CREATE VIEW v_sales AS
        SELECT oi.item_id, o.order_id, o.order_date, o.ship_mode,
               c.customer_id, c.customer_name, c.segment, c.region, c.state,
               p.product_id, p.product_name, p.category, p.sub_category,
               oi.sales, oi.quantity, oi.discount, oi.profit
        FROM order_items oi
        JOIN orders o    ON o.order_id = oi.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN products p  ON p.product_id = oi.product_id
    """)
    con.commit()
    con.close()
    print("database ready:", DB_PATH)


def connect_ro():
    """Read-only connection. Even if bad SQL slips through, it can't write."""
    return sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)


if __name__ == "__main__":
    import sys
    build_db(sys.argv[1] if len(sys.argv) > 1 else "data/superstore.csv")
