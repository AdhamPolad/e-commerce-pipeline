"""Stage 2a: build a deliberately DIRTY sales CSV that uses real product IDs.

Injected problems: exact duplicates, missing values, wrong data types
(text numbers, '$' prices, number words), mixed date formats, invalid dates,
unknown product IDs, non-positive quantities, messy e-mails / names / countries.
"""
import random

import pandas as pd

from src import config

FIRST = ["Aigerim", "Bekzod", "Camila", "Dara", "Elena", "Farid", "Gulnara",
         "Hana", "Ivan", "Jin", "Kamala", "Lina", "Minh", "Nodira", "Omar"]
LAST = ["Karimova", "Tashev", "Lopez", "Sok", "Petrova", "Aliyev", "Nurova",
        "Kim", "Smirnov", "Park", "Rahman", "Chea", "Nguyen", "Yusupova", "Haddad"]
COUNTRIES = ["Azerbaijan", "Uzbekistan", "Cambodia", "Vietnam", "Korea", "Kazakhstan"]


def generate(products: pd.DataFrame, n_orders: int = 120, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    customers = []
    for cid in range(1, 26):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        email = f"{name.lower().replace(' ', '.')}{cid}@example.com"
        customers.append((cid, name, email, rng.choice(COUNTRIES)))

    prices = dict(zip(products["product_id"], products["price"]))
    ids = list(prices)
    rows = []
    for order_id in range(1001, 1001 + n_orders):
        cid, name, email, country = rng.choice(customers)
        date = pd.Timestamp("2026-01-01") + pd.Timedelta(days=rng.randint(0, 300))
        for pid in rng.sample(ids, rng.randint(1, 3)):
            rows.append({
                "order_id": order_id, "order_date": date.strftime("%Y-%m-%d"),
                "customer_id": cid, "customer_name": name, "customer_email": email,
                "country": country, "product_id": pid, "quantity": rng.randint(1, 5),
                "unit_price": f"{prices[pid]:.2f}",
            })
    df = pd.DataFrame(rows).astype(str)

    def pick(k):
        return list(df.sample(k, random_state=rng.randint(0, 10_000)).index)

    # --- inject problems ---------------------------------------------------
    df.loc[pick(8), "unit_price"] = ""                       # missing price
    df.loc[pick(5), "quantity"] = ""                         # missing quantity
    df.loc[pick(4), "customer_id"] = ""                      # missing customer id
    df.loc[pick(6), "country"] = ""                          # missing country
    df.loc[pick(5), "customer_name"] = ""                    # missing name
    df.loc[pick(6), "customer_email"] = ""                   # missing email
    for i in pick(6):                                        # '$' prices (wrong type)
        if df.loc[i, "unit_price"]:
            df.loc[i, "unit_price"] = "$" + df.loc[i, "unit_price"]
    for i in pick(5):                                        # quantity as words / text
        df.loc[i, "quantity"] = rng.choice(["two", "three", "one", " 2 ", "4.0"])
    for i in pick(4):                                        # impossible quantity
        df.loc[i, "quantity"] = rng.choice(["0", "-1", "-3"])
    for i in pick(12):                                       # mixed date formats
        d = pd.Timestamp(df.loc[i, "order_date"])
        df.loc[i, "order_date"] = rng.choice([d.strftime("%d %b %Y"), d.strftime("%Y/%m/%d")])
    df.loc[pick(3), "order_date"] = "not a date"             # invalid date
    df.loc[pick(5), "product_id"] = "9999"                   # unknown product ID
    for i in pick(8):                                        # messy text
        df.loc[i, "customer_email"] = rng.choice(
            ["  " + df.loc[i, "customer_email"].upper() + " ", "no-at-sign.example.com"])
        df.loc[i, "customer_name"] = df.loc[i, "customer_name"].upper()
    for i in pick(5):
        df.loc[i, "country"] = " " + df.loc[i, "country"].lower() + " "

    dupes = df.sample(10, random_state=1)                    # exact duplicate rows
    df = pd.concat([df, dupes], ignore_index=True)
    return df.sample(frac=1, random_state=7).reset_index(drop=True)


def run() -> pd.DataFrame:
    products = pd.read_parquet(config.PRODUCTS_PARQUET)
    df = generate(products)
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.SALES_RAW_CSV, index=False)
    return df
