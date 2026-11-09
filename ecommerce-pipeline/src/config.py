"""Central configuration: paths, API URL and database settings."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"

PRODUCTS_PARQUET = RAW_DIR / "products.parquet"
SALES_RAW_CSV = RAW_DIR / "sales_raw.csv"
SALES_CLEAN_CSV = PROCESSED_DIR / "sales_clean.csv"
SALES_REJECTED_CSV = PROCESSED_DIR / "sales_rejected.csv"

API_URL = "https://dummyjson.com/products"
API_LIMIT = 50  # product IDs 1..50

DB = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "ecommerce"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}
