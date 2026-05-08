from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path

from pymongo.errors import PyMongoError

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db import retail_analytics_collection


CSV_PATH = Path(__file__).resolve().parent.parent / "documents" / "retail_analytics_data.csv"


def load_csv_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with CSV_PATH.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(
                {
                    "date": row["date"],
                    "product": row["product"],
                    "category": row["category"],
                    "price": float(row["price"]),
                    "stock": int(row["stock"]),
                    "sales": float(row["sales"]),
                    "orders": int(row["orders"]),
                    "rating": float(row["rating"]),
                }
            )
    return rows


def upsert_rows(rows: list[dict[str, object]]) -> None:
    completed = 0
    for row in rows:
        for attempt in range(5):
            try:
                retail_analytics_collection.replace_one(
                    {"date": row["date"], "product": row["product"]},
                    row,
                    upsert=True,
                )
                completed += 1
                time.sleep(0.12)
                break
            except PyMongoError as exc:
                if attempt == 4:
                    raise
                print(f"Retrying {row['product']} on {row['date']} after error: {exc}")
                time.sleep(0.8 + (attempt * 0.6))
    print(f"Processed {completed} rows.")


def main() -> None:
    if not CSV_PATH.exists():
        print(f"CSV file not found: {CSV_PATH}")
        return

    rows = load_csv_rows()
    if not rows:
        print("No analytics rows found in CSV.")
        return

    upsert_rows(rows)
    print(f"Loaded {len(rows)} rows into Cosmos collection: retail_analytics")


if __name__ == "__main__":
    main()
