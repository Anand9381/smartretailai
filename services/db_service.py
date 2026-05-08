from __future__ import annotations

import math
from collections import defaultdict

from db import orders_collection, products_collection, retail_analytics_collection


class DBService:
    def get_products(self) -> list[dict]:
        return list(products_collection.find({}, {"_id": 0}))

    def filter_products(self, message: str) -> list[dict]:
        products = self.get_products()
        message_lower = message.lower()
        category_keywords = {
            "electronics": "Electronics",
            "fashion": "Fashion",
            "travel": "Travel",
            "sports": "Sports",
            "kitchen": "Home & Kitchen",
            "home": "Home & Kitchen",
        }

        max_price = None
        digits = "".join(ch if ch.isdigit() else " " for ch in message_lower).split()
        if digits:
            max_price = max(int(value) for value in digits)

        filtered = []
        for product in products:
            if "stock available" in message_lower and int(product.get("stock", 0)) <= 0:
                continue
            category_match = True
            for keyword, category in category_keywords.items():
                if keyword in message_lower:
                    category_match = product.get("category") == category
                    break
            if not category_match:
                continue
            if max_price is not None and float(product.get("price", 0)) > max_price:
                continue
            filtered.append(product)
        return filtered[:6]

    def recommend_products(self, message: str) -> list[dict]:
        candidates = self.filter_products(message)
        if candidates:
            return sorted(candidates, key=lambda item: (item.get("stock", 0), item.get("price", 0)), reverse=True)[:4]
        return sorted(self.get_products(), key=lambda item: (item.get("stock", 0), item.get("price", 0)), reverse=True)[:4]

    def find_products_from_history(self, chat_history: list[dict]) -> list[dict]:
        products = self.get_products()
        matched = []
        for turn in reversed(chat_history):
            content = turn.get("content", "").lower()
            for product in products:
                if product["name"].lower() in content and product not in matched:
                    matched.append(product)
            if len(matched) >= 4:
                break
        return matched[:4]

    def get_analytics_rows(self) -> list[dict]:
        return list(retail_analytics_collection.find({}, {"_id": 0}))

    def summarize_analytics(self) -> dict:
        rows = self.get_analytics_rows()
        if not rows:
            return {
                "top_category": "No analytics data",
                "trending_products": [],
                "low_stock_products": [],
                "sales_spikes": [],
            }

        category_sales = defaultdict(float)
        product_sales = defaultdict(list)
        latest_stock = {}
        for row in rows:
            category_sales[row["category"]] += float(row["sales"])
            product_sales[row["product"]].append(float(row["sales"]))
            latest_stock[row["product"]] = int(row["stock"])

        growth_scores = []
        spikes = []
        for product, sales_values in product_sales.items():
            midpoint = max(1, len(sales_values) // 2)
            first_half = sum(sales_values[:midpoint])
            second_half = sum(sales_values[midpoint:])
            growth = second_half - first_half
            growth_scores.append((product, growth))

            avg = sum(sales_values) / len(sales_values)
            variance = sum((value - avg) ** 2 for value in sales_values) / len(sales_values)
            threshold = avg + (2 * math.sqrt(variance))
            if any(value > threshold for value in sales_values):
                spikes.append(product)

        low_stock = [product for product, stock in latest_stock.items() if stock <= 20]
        top_category = max(category_sales.items(), key=lambda item: item[1])[0]
        trending_products = [name for name, _ in sorted(growth_scores, key=lambda item: item[1], reverse=True)[:3]]

        return {
            "top_category": top_category,
            "trending_products": trending_products,
            "low_stock_products": low_stock[:5],
            "sales_spikes": spikes[:5],
        }

    def get_order_stats(self) -> dict:
        orders = list(orders_collection.find({}, {"_id": 0, "items": 1, "total": 1, "status": 1}))
        revenue = sum(float(order.get("total", 0)) for order in orders)
        total_orders = len(orders)
        return {"total_orders": total_orders, "revenue": revenue}


db_service = DBService()
