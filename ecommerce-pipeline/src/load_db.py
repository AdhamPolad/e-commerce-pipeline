"""Stage 3: create the schema and load products (Parquet) + cleaned sales tables."""
import logging

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src import config
from src.clean_sales import split_tables

log = logging.getLogger(__name__)


def _rows(df: pd.DataFrame, cols: list[str]) -> list[tuple]:
    """DataFrame -> list of tuples with NaN/NA converted to None and numpy ints to int."""
    out = []
    for rec in df[cols].astype(object).where(df[cols].notna(), None).itertuples(index=False):
        out.append(tuple(v.item() if hasattr(v, "item") else v for v in rec))
    return out


def load(clean: pd.DataFrame, products: pd.DataFrame, recreate: bool = True) -> dict:
    tables = split_tables(clean)
    with psycopg2.connect(**config.DB) as conn, conn.cursor() as cur:
        if recreate:
            cur.execute((config.SQL_DIR / "schema.sql").read_text())

        # parents first, children last -> foreign keys are always satisfied
        execute_values(cur, """
            INSERT INTO products (product_id,title,category,brand,price,stock,rating) VALUES %s
            ON CONFLICT (product_id) DO UPDATE SET title=EXCLUDED.title,
              category=EXCLUDED.category, brand=EXCLUDED.brand, price=EXCLUDED.price,
              stock=EXCLUDED.stock, rating=EXCLUDED.rating""",
            _rows(products, ["product_id", "title", "category", "brand", "price", "stock", "rating"]))
        execute_values(cur, """
            INSERT INTO customers (customer_id,full_name,email,country) VALUES %s
            ON CONFLICT (customer_id) DO UPDATE SET full_name=EXCLUDED.full_name,
              email=EXCLUDED.email, country=EXCLUDED.country""",
            _rows(tables["customers"], ["customer_id", "full_name", "email", "country"]))
        execute_values(cur, """
            INSERT INTO orders (order_id,customer_id,order_date) VALUES %s
            ON CONFLICT (order_id) DO NOTHING""",
            _rows(tables["orders"], ["order_id", "customer_id", "order_date"]))
        execute_values(cur, """
            INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES %s
            ON CONFLICT (order_id,product_id) DO UPDATE SET quantity=EXCLUDED.quantity,
              unit_price=EXCLUDED.unit_price""",
            _rows(tables["order_items"], ["order_id", "product_id", "quantity", "unit_price"]))

        counts = {}
        for t in ["products", "customers", "orders", "order_items"]:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
    log.info("Loaded rows: %s", counts)
    return counts


def run() -> dict:
    products = pd.read_parquet(config.PRODUCTS_PARQUET)
    clean = pd.read_csv(config.SALES_CLEAN_CSV, parse_dates=["order_date"])
    clean["order_date"] = clean["order_date"].dt.date
    clean = clean.astype(object).where(clean.notna(), None)
    return load(clean, products)


def demo_query() -> pd.DataFrame:
    sql = (config.SQL_DIR / "queries.sql").read_text().split(";")[0]
    with psycopg2.connect(**config.DB) as conn:
        return pd.read_sql_query(sql, conn)
