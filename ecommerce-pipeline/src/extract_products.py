"""Stage 1: fetch products from the public DummyJSON REST API -> Parquet."""
import logging
import time

import pandas as pd
import requests

from src import config

log = logging.getLogger(__name__)
COLUMNS = ["product_id", "title", "category", "brand", "price", "stock", "rating"]


def fetch_products(url: str = config.API_URL, limit: int = config.API_LIMIT,
                   retries: int = 3) -> list[dict]:
    """GET the product list, retrying on network errors."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params={"limit": limit}, timeout=15)
            resp.raise_for_status()
            return resp.json()["products"]
        except (requests.RequestException, KeyError, ValueError) as exc:
            log.warning("API attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)


def to_dataframe(products: list[dict]) -> pd.DataFrame:
    """Flatten the JSON into a tidy, typed table."""
    df = pd.DataFrame(products).rename(columns={"id": "product_id"})
    if "brand" not in df:  # some products have no brand
        df["brand"] = None
    df = df[COLUMNS].copy()
    df["product_id"] = df["product_id"].astype("int64")
    df["price"] = df["price"].astype("float64").round(2)
    df["stock"] = df["stock"].astype("int64")
    df["rating"] = df["rating"].astype("float64").round(2)
    return df.drop_duplicates("product_id").sort_values("product_id").reset_index(drop=True)


def run() -> pd.DataFrame:
    df = to_dataframe(fetch_products())
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.PRODUCTS_PARQUET, index=False)
    log.info("Saved %d products to %s", len(df), config.PRODUCTS_PARQUET)
    return df
