"""
etl_pipeline.py - simple ETL to load CSVs into a PostgreSQL database.

Usage:
  - Set the DB_URL environment variable or edit the DB_URL in the script.
  - python etl_pipeline.py

Notes:
  - This script expects the CSVs to be in the "data/" folder at the same level as the script.
  - It will insert customers, products, orders (storing order_external_id), then order_items (mapping SKUs -> product_id and order_external_id -> order_id),
    and shipments (mapping external -> internal order_id).
  - For production use, add transactions, retries, and more robust error handling.
"""
import os, sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://user:password@localhost:5432/salesdb")

DATA_DIR = "data"
CUSTOMERS_CSV = os.path.join(DATA_DIR, "customers.csv")
PRODUCTS_CSV = os.path.join(DATA_DIR, "products.csv")
ORDERS_CSV = os.path.join(DATA_DIR, "orders.csv")
ORDER_ITEMS_CSV = os.path.join(DATA_DIR, "order_items.csv")
SHIPMENTS_CSV = os.path.join(DATA_DIR, "shipments.csv")

def read_csv_check(path, expected_cols):
    df = pd.read_csv(path)
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"CSV {path} missing columns: {missing}")
    return df

def main():
    print("Connecting to DB:", DB_URL)
    engine = create_engine(DB_URL, echo=False)
    conn = engine.connect()
    try:
        # 1. Load customers
        cust_cols = ["email","full_name","signup_date","country"]
        customers = read_csv_check(CUSTOMERS_CSV, cust_cols)
        customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce").dt.date
        customers = customers.drop_duplicates(subset=["email"])
        customers.to_sql("customers", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        print(f"Inserted customers: {len(customers)}")

        # 2. Load products
        prod_cols = ["sku","name","category","price"]
        products = read_csv_check(PRODUCTS_CSV, prod_cols)
        products["price"] = pd.to_numeric(products["price"], errors="coerce")
        products = products.drop_duplicates(subset=["sku"])
        products.to_sql("products", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        print(f"Inserted products: {len(products)}")

        # 3. Load orders (store external id)
        ord_cols = ["order_external_id","customer_email","order_date","status","total_amount"]
        orders = read_csv_check(ORDERS_CSV, ord_cols)
        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
        orders["total_amount"] = pd.to_numeric(orders["total_amount"], errors="coerce")

        # map customer_email -> customer_id
        cust_df = pd.read_sql("SELECT customer_id, email FROM customers", engine)
        orders = orders.merge(cust_df, left_on="customer_email", right_on="email", how="left")
        missing_customers = orders[orders["customer_id"].isna()]
        if not missing_customers.empty:
            print("ERROR: Some orders reference missing customers. Aborting ETL.")
            print(missing_customers.head())
            sys.exit(1)

        orders_db = orders[["order_external_id","customer_id","order_date","status","total_amount"]].copy()
        orders_db.to_sql("orders", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        print(f"Inserted orders: {len(orders_db)}")

        # 4. Load order_items (map sku -> product_id, external order id -> order_id)
        oi_cols = ["order_external_id","sku","quantity","unit_price"]
        order_items = read_csv_check(ORDER_ITEMS_CSV, oi_cols)
        prod_df = pd.read_sql("SELECT product_id, sku FROM products", engine)
        order_items = order_items.merge(prod_df, on="sku", how="left")
        if order_items["product_id"].isna().any():
            print("ERROR: Some SKUs in order_items are missing in products table. Aborting.")
            print(order_items[order_items['product_id'].isna()].head())
            sys.exit(1)

        # Map order_external_id -> order_id (read mapping from orders table)
        mapping = pd.read_sql("SELECT order_id, order_external_id FROM orders", engine)
        order_items = order_items.merge(mapping, on="order_external_id", how="left")
        if order_items["order_id"].isna().any():
            print("ERROR: Some order_external_id values in order_items are missing in orders table. Aborting.")
            print(order_items[order_items['order_id'].isna()].head())
            sys.exit(1)

        order_items["line_total"] = order_items["quantity"].astype(int) * order_items["unit_price"].astype(float)
        order_items_db = order_items[["order_id","product_id","quantity","unit_price","line_total"]].copy()
        order_items_db.to_sql("order_items", engine, if_exists="append", index=False, method="multi", chunksize=2000)
        print(f"Inserted order_items: {len(order_items_db)}")

        # 5. Load shipments (map order_external_id -> order_id)
        ship_cols = ["order_external_id","shipped_date","delivery_date","carrier","tracking_number"]
        if os.path.exists(SHIPMENTS_CSV):
            shipments = read_csv_check(SHIPMENTS_CSV, ship_cols)
            shipments = shipments.merge(mapping, on="order_external_id", how="left")
            shipments_db = shipments[["order_id","shipped_date","delivery_date","carrier","tracking_number"]].copy()
            shipments_db.to_sql("shipments", engine, if_exists="append", index=False, method="multi", chunksize=1000)
            print(f"Inserted shipments: {len(shipments_db)}")

        print("ETL completed successfully.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
