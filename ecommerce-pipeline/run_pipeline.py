"""Run the whole pipeline:  python run_pipeline.py [--stage extract|sales|clean|load|all]"""
import argparse
import json
import logging

from src import clean_sales, extract_products, generate_sales, load_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=["extract", "sales", "clean", "load", "all"])
    stage = ap.parse_args().stage

    if stage in ("extract", "all"):
        extract_products.run()
    if stage in ("sales", "all"):
        generate_sales.run()
    if stage in ("clean", "all"):
        result = clean_sales.run()
        print("\n=== CLEANING REPORT ===\n" + json.dumps(result.report, indent=2))
    if stage in ("load", "all"):
        load_db.run()
        print("\n=== TOTAL SALES VALUE BY PRODUCT (top 10) ===")
        print(load_db.demo_query().to_string(index=False))


if __name__ == "__main__":
    main()
