"""Smoke test for `ml_model.py`.

Creates a small sample dataset if needed, then exercises prediction and
anomaly detection.
"""
import os
import csv
from datetime import datetime, timedelta
from random import Random


def _ensure_csv(path='data/sales_data.csv'):
    if os.path.exists(path):
        print(f"Found existing dataset at {path}")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = datetime(2024, 1, 1)
    rows = []
    rng = Random(42)

    for i in range(90):
        date = start + timedelta(days=i)
        base = 50 + 0.5 * i
        seasonal = 8 * (1 + (i % 30) / 30)
        noise = rng.gauss(0, 5)
        sales = max(0, base + seasonal + noise)
        rows.append((date.strftime("%Y-%m-%d"), round(sales, 2)))

    rows[30] = (rows[30][0], rows[30][1] + 80)  # spike
    rows[60] = (rows[60][0], max(0, rows[60][1] - 60))  # dip

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["date", "sales"])
        writer.writerows(rows)
    print(f"Generated dataset with {len(rows)} rows at {path}")


def main():
    _ensure_csv()

    try:
        import ml_model
    except Exception as e:
        print("Failed to import ml_model:", e)
        return

    print("\nPredict sales for day index 0:", ml_model.predict_sales(0))
    print("Predict sales for 2024-01-15:", ml_model.predict_sales("2024-01-15"))

    anomalies = ml_model.detect_anomalies()
    print(f"Found {len(anomalies)} anomalies:")
    if not anomalies.empty:
        print(anomalies.to_string(index=False))


if __name__ == "__main__":
    main()
