"""Stage 2b: detect and fix problems in the raw sales CSV.

Policy
------
* Identifiers / quantity / date are essential -> if missing or unfixable the row is
  REJECTED (written to sales_rejected.csv with a reason, never silently lost).
* Fixable problems are CORRECTED (whitespace, '$', number words, date formats, casing).
* Missing unit_price is IMPUTED from the product catalogue.
* Missing optional attributes (email, country, name) become NULL / 'Unknown'.
"""
from dataclasses import dataclass, field

import pandas as pd

from src import config

NULL_TOKENS = {"", "na", "n/a", "null", "none", "nan", "-"}
WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
DATE_FORMATS = ["%Y-%m-%d", "%d %b %Y", "%Y/%m/%d"]
EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
REQUIRED = ["order_id", "customer_id", "product_id", "order_date", "quantity"]


@dataclass
class CleanResult:
    clean: pd.DataFrame
    rejected: pd.DataFrame
    report: dict = field(default_factory=dict)


def parse_dates(s: pd.Series) -> pd.Series:
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        out = out.fillna(pd.to_datetime(s, format=fmt, errors="coerce"))
    return out


def clean_sales(raw: pd.DataFrame, catalog: pd.DataFrame) -> CleanResult:
    report: dict = {"rows_in": len(raw)}
    rejected: list[pd.DataFrame] = []
    df = raw.copy()

    def reject(mask: pd.Series, reason: str, key: str) -> None:
        nonlocal df
        report[key] = int(mask.sum())
        if mask.any():
            rejected.append(df[mask].assign(reject_reason=reason))
        df = df[~mask].copy()

    # 1. normalise headers + whitespace + null tokens (everything starts as text)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.astype("string")
    for c in df.columns:
        df[c] = df[c].str.strip()
        df.loc[df[c].str.lower().isin(NULL_TOKENS), c] = pd.NA
    report["missing_before"] = {c: int(n) for c, n in df.isna().sum().items() if n}

    # 2. exact duplicate rows
    reject(df.duplicated(keep="first"), "exact duplicate row", "exact_duplicates_removed")

    # 3. essential fields missing
    reject(df[REQUIRED].isna().any(axis=1), "missing essential field", "missing_essential_rejected")

    # 4. wrong data types -> convert
    for col in ["order_id", "customer_id", "product_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    bad_id = df[["order_id", "customer_id", "product_id"]].isna().any(axis=1)
    reject(bad_id, "non-numeric id", "bad_ids_rejected")
    for col in ["order_id", "customer_id", "product_id"]:
        df[col] = df[col].astype("int64")

    q_text = df["quantity"].str.lower()
    q_fixed = q_text.map(WORD_NUMBERS).astype("Float64")
    df["quantity"] = pd.to_numeric(q_text, errors="coerce").astype("Float64").fillna(q_fixed)
    report["quantity_words_fixed"] = int(q_fixed.notna().sum())
    reject(df["quantity"].isna() | (df["quantity"] <= 0) | (df["quantity"] % 1 != 0),
           "invalid quantity", "invalid_quantity_rejected")
    df["quantity"] = df["quantity"].astype("int64")

    df["unit_price"] = pd.to_numeric(df["unit_price"].str.replace(r"[$,\s]", "", regex=True),
                                     errors="coerce")
    # 5. impute missing price from catalogue
    prices = catalog.set_index("product_id")["price"]
    missing_price = df["unit_price"].isna()
    df.loc[missing_price, "unit_price"] = df.loc[missing_price, "product_id"].map(prices)
    report["price_imputed_from_catalogue"] = int(missing_price.sum())
    reject(df["unit_price"].isna() | (df["unit_price"] <= 0), "invalid price", "invalid_price_rejected")
    df["unit_price"] = df["unit_price"].astype(float).round(2)

    df["order_date"] = parse_dates(df["order_date"])
    reject(df["order_date"].isna() | (df["order_date"] > pd.Timestamp.today()),
           "invalid or future date", "invalid_date_rejected")

    # 6. referential check against API products
    reject(~df["product_id"].isin(catalog["product_id"]), "unknown product_id", "unknown_product_rejected")

    # 7. text standardisation
    df["customer_email"] = df["customer_email"].str.lower()
    bad_email = df["customer_email"].notna() & ~df["customer_email"].str.match(EMAIL_RE, na=False)
    df.loc[bad_email, "customer_email"] = pd.NA
    report["invalid_emails_nulled"] = int(bad_email.sum())
    df["customer_name"] = df["customer_name"].str.title()
    df["country"] = df["country"].str.title()

    # fill gaps from other rows of the same customer, then default
    for col in ["customer_name", "customer_email", "country"]:
        have = df.dropna(subset=[col])
        gaps = df[col].isna()
        if have.empty or not gaps.any():
            continue
        known = have.groupby("customer_id")[col].agg(lambda s: s.mode().iloc[0])
        df.loc[gaps, col] = df.loc[gaps, "customer_id"].map(known).astype("string")
    df["customer_name"] = df["customer_name"].fillna("Unknown")
    df["country"] = df["country"].fillna("Unknown")

    # 8. one line per (order, product)
    reject(df.duplicated(["order_id", "product_id"], keep="first"),
           "duplicate order line", "duplicate_order_lines_removed")

    df["order_date"] = df["order_date"].dt.date
    df = df.sort_values(["order_id", "product_id"]).reset_index(drop=True)
    for c in ["customer_name", "customer_email", "country"]:
        df[c] = df[c].astype(object).where(df[c].notna(), None)

    rej = pd.concat(rejected, ignore_index=True) if rejected else pd.DataFrame()
    report["rows_out"] = len(df)
    report["rows_rejected"] = len(rej)
    return CleanResult(df, rej, report)


def split_tables(clean: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Normalise the flat sales table into customers / orders / order_items."""
    customers = (clean.groupby("customer_id", as_index=False)
                 .agg(full_name=("customer_name", "first"),
                      email=("customer_email", lambda s: s.dropna().iloc[0] if s.notna().any() else None),
                      country=("country", "first")))
    orders = (clean.sort_values("order_date")
              .drop_duplicates("order_id")[["order_id", "customer_id", "order_date"]])
    items = clean[["order_id", "product_id", "quantity", "unit_price"]]
    return {"customers": customers, "orders": orders, "order_items": items}


def run() -> CleanResult:
    raw = pd.read_csv(config.SALES_RAW_CSV, dtype=str, keep_default_na=False)
    catalog = pd.read_parquet(config.PRODUCTS_PARQUET)
    result = clean_sales(raw, catalog)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    result.clean.to_csv(config.SALES_CLEAN_CSV, index=False)
    result.rejected.to_csv(config.SALES_REJECTED_CSV, index=False)
    return result
