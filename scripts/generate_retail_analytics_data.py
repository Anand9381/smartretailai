from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "documents" / "retail_analytics_data.csv"


PRODUCTS = [
    {
        "product": "Wireless Headphones Pro",
        "category": "Electronics",
        "price": 199,
        "rating": 4.6,
        "start_stock": 140,
        "base_units": 6,
        "daily_growth": 0.45,
        "spikes": {12: 10, 15: 8},
        "restocks": {10: 35},
    },
    {
        "product": "Smart Watch Ultra",
        "category": "Electronics",
        "price": 349,
        "rating": 4.7,
        "start_stock": 92,
        "base_units": 4,
        "daily_growth": 0.35,
        "spikes": {9: 4, 14: 6},
        "restocks": {11: 18},
    },
    {
        "product": "Designer Sunglasses",
        "category": "Fashion",
        "price": 129,
        "rating": 4.4,
        "start_stock": 120,
        "base_units": 5,
        "daily_growth": 0.18,
        "spikes": {6: 4, 13: 5},
        "restocks": {16: 20},
    },
    {
        "product": "Premium Coffee Maker",
        "category": "Home & Kitchen",
        "price": 89,
        "rating": 4.1,
        "start_stock": 110,
        "base_units": 8,
        "daily_growth": -0.32,
        "spikes": {5: 5},
        "restocks": {},
    },
    {
        "product": "Wireless Earbuds Air",
        "category": "Electronics",
        "price": 149,
        "rating": 4.8,
        "start_stock": 160,
        "base_units": 9,
        "daily_growth": 0.5,
        "spikes": {8: 14, 16: 12},
        "restocks": {9: 40},
    },
    {
        "product": "Fitness Band Pro",
        "category": "Sports",
        "price": 79,
        "rating": 4.5,
        "start_stock": 130,
        "base_units": 4,
        "daily_growth": 0.38,
        "spikes": {11: 6},
        "restocks": {14: 25},
    },
    {
        "product": "Urban Travel Backpack",
        "category": "Travel",
        "price": 119,
        "rating": 4.3,
        "start_stock": 88,
        "base_units": 3,
        "daily_growth": 0.28,
        "spikes": {12: 8, 13: 5},
        "restocks": {15: 16},
    },
]


def generate_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start = date(2026, 4, 1)
    days = 18

    for product_index, product in enumerate(PRODUCTS):
        sold_so_far = 0
        for day_offset in range(days):
            current_date = start + timedelta(days=day_offset)
            units = max(1, round(product["base_units"] + (product["daily_growth"] * day_offset)))
            units += product["spikes"].get(day_offset, 0)

            if day_offset in product["restocks"]:
                sold_so_far -= product["restocks"][day_offset]

            stock = max(4, int(product["start_stock"] - sold_so_far))
            sales = units * product["price"]
            orders = max(1, round(units * 0.55))
            rating = round(product["rating"] + (((day_offset + product_index) % 3) - 1) * 0.1, 1)
            rating = min(4.9, max(3.8, rating))

            rows.append(
                {
                    "date": current_date.isoformat(),
                    "product": product["product"],
                    "category": product["category"],
                    "price": float(product["price"]),
                    "stock": stock,
                    "sales": float(sales),
                    "orders": int(orders),
                    "rating": rating,
                }
            )
            sold_so_far += units
    return rows


def write_csv(rows: list[dict[str, object]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date", "product", "category", "price", "stock", "sales", "orders", "rating"]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = generate_rows()
    write_csv(rows)
    print(f"Created {OUTPUT_PATH} with {len(rows)} rows.")


if __name__ == "__main__":
    main()
