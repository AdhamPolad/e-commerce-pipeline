import pandas as pd

from src.clean_sales import clean_sales, split_tables
from src.generate_sales import generate

CATALOG = pd.DataFrame({"product_id": range(1, 51), "price": [10.0 + i for i in range(50)]})


def _row(**kw):
    base = dict(order_id="1", order_date="2026-03-01", customer_id="1",
                customer_name="Ann Lee", customer_email="ann@example.com",
                country="Korea", product_id="1", quantity="2", unit_price="10.00")
    base.update(kw)
    return base


def test_exact_duplicates_removed():
    raw = pd.DataFrame([_row(), _row()])
    res = clean_sales(raw, CATALOG)
    assert len(res.clean) == 1 and res.report["exact_duplicates_removed"] == 1


def test_types_are_fixed():
    raw = pd.DataFrame([_row(quantity="two", unit_price="$1,010.50", order_date="05 Mar 2026")])
    row = clean_sales(raw, CATALOG).clean.iloc[0]
    assert row.quantity == 2 and row.unit_price == 1010.50
    assert str(row.order_date) == "2026-03-05"


def test_missing_price_imputed_and_missing_quantity_rejected():
    raw = pd.DataFrame([_row(unit_price=""), _row(order_id="2", quantity="")])
    res = clean_sales(raw, CATALOG)
    assert res.clean.iloc[0].unit_price == 10.0
    assert res.report["missing_essential_rejected"] == 1


def test_bad_rows_rejected_with_reason():
    raw = pd.DataFrame([_row(order_id="3", product_id="9999"),
                        _row(order_id="4", quantity="-1"),
                        _row(order_id="5", order_date="not a date")])
    res = clean_sales(raw, CATALOG)
    assert res.clean.empty
    assert set(res.rejected["reject_reason"]) == {"unknown product_id", "invalid quantity",
                                                  "invalid or future date"}


def test_text_standardised():
    raw = pd.DataFrame([_row(customer_name="ANN LEE", customer_email="  BAD-EMAIL ", country=" korea ")])
    row = clean_sales(raw, CATALOG).clean.iloc[0]
    assert row.customer_name == "Ann Lee" and row.country == "Korea" and row.customer_email is None


def test_full_generated_dataset_ends_consistent():
    raw = generate(CATALOG.assign(price=CATALOG["price"]))
    res = clean_sales(raw, CATALOG)
    c = res.clean
    assert not c.duplicated(["order_id", "product_id"]).any()
    assert c["product_id"].isin(CATALOG["product_id"]).all()
    assert (c["quantity"] > 0).all() and (c["unit_price"] > 0).all()
    t = split_tables(c)
    assert set(t["orders"]["customer_id"]) <= set(t["customers"]["customer_id"])
    assert t["orders"]["order_id"].is_unique
