import json
import os
from typing import Optional

from services.llm_service import LLMService


class ProductMonitoringAgent:
    """Admin-only product monitoring answers grounded in local project data."""

    def __init__(self):
        self.llm_service = LLMService()
        self._data = self._load_json("product_monitoring_data.json")

    def _load_json(self, filename: str) -> list[dict]:
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", filename))
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        message = user_message.strip()
        if not message:
            return "Ask me about product stock, trending items, active offers, cart adds, views, or monitoring alerts."
        if not self._data:
            return "No monitoring data available for this request."

        text = message.lower()
        if self._is_out_of_domain(text):
            return "I am here only for SmartRetailAI admin product monitoring: stock, trends, offers, views, carts, and product performance."

        if any(word in text for word in ["trend", "trending", "popular", "demand", "selling fast", "best product"]):
            return self._humanise(message, self._trending())
        if any(word in text for word in ["low stock", "critical", "alert", "attention", "running low", "almost over", "nearly finished", "stock risk"]):
            return self._humanise(message, self._low_stock())
        if any(word in text for word in ["out of stock", "sold out", "unavailable"]):
            return self._humanise(message, self._out_of_stock())
        if any(word in text for word in ["offer", "discount", "coupon", "deal", "promo", "campaign"]):
            return self._humanise(message, self._active_offers())
        if any(word in text for word in ["cart", "added to cart", "cart adds", "most added"]):
            return self._humanise(message, self._cart_leaders())
        if any(word in text for word in ["view", "views", "traffic", "engagement", "visited", "most viewed"]):
            return self._humanise(message, self._view_leaders())
        if any(word in text for word in ["performance", "performing", "best", "top"]):
            return self._humanise(message, self._performance())
        if matched := self._find_product(text):
            return self._humanise(message, self._product_snapshot(matched))
        return self._humanise(message, self._overview())

    def _humanise(self, message: str, fallback: str) -> str:
        return self.llm_service.grounded_answer(
            message,
            fallback,
            "admin product monitoring assistant",
            fallback=fallback,
        )

    def _is_out_of_domain(self, text: str) -> bool:
        blocked = [
            "capital of", "weather", "news", "prime minister", "president", "cricket",
            "football", "bitcoin", "stock market", "python code", "recipe",
        ]
        return any(word in text for word in blocked)

    def _find_product(self, text: str) -> Optional[dict]:
        for product in self._data:
            name = product.get("name", "").lower()
            if name and name in text:
                return product
        return None

    def _sort(self, key: str, reverse: bool = True) -> list[dict]:
        return sorted(self._data, key=lambda p: float(p.get(key) or 0), reverse=reverse)

    def _trending(self) -> str:
        products = self._sort("trendingScore")[:5]
        lines = ["Current trending products from the app dataset:"]
        for product in products:
            lines.append(
                f"- {product['name']}: trend score {product['trendingScore']}, "
                f"{product['views']} views, {product['cartAdds']} cart adds, stock {product['stock']} ({product['stockStatus']})."
            )
        return "\n".join(lines)

    def _low_stock(self) -> str:
        products = [p for p in self._data if p.get("stockStatus") in {"Low Stock", "Critical Stock", "Out Of Stock"}]
        if not products:
            return "No low-stock alerts right now. All monitored products have healthy stock."
        lines = ["Stock alerts that need admin attention:"]
        for product in sorted(products, key=lambda p: p.get("stock", 0)):
            lines.append(
                f"- {product['name']}: {product['stock']} units, {product['stockStatus']}, "
                f"trend score {product['trendingScore']}."
            )
        return "\n".join(lines)

    def _out_of_stock(self) -> str:
        products = [p for p in self._data if p.get("stockStatus") == "Out Of Stock"]
        if not products:
            return "No monitored product is marked out of stock."
        return "Out-of-stock products:\n" + "\n".join(f"- {p['name']}: {p['cartAdds']} cart adds lost while stock is 0." for p in products)

    def _active_offers(self) -> str:
        products = [p for p in self._data if self._has_offer(p)]
        if not products:
            return "No active product offers are present in the monitoring dataset."
        lines = ["Active offers in the app catalog:"]
        for product in products:
            lines.append(
                f"- {product['name']}: {product['activeOffer']} | trend {product['trendingScore']} | cart adds {product['cartAdds']}."
            )
        return "\n".join(lines)

    def _cart_leaders(self) -> str:
        products = self._sort("cartAdds")[:5]
        return "Most added-to-cart products:\n" + "\n".join(
            f"- {p['name']}: {p['cartAdds']} cart adds, {p['views']} views, stock {p['stock']}."
            for p in products
        )

    def _view_leaders(self) -> str:
        products = self._sort("views")[:5]
        return "Highest-view products:\n" + "\n".join(
            f"- {p['name']}: {p['views']} views, trend score {p['trendingScore']}, performance {p['performance']}."
            for p in products
        )

    def _performance(self) -> str:
        products = self._sort("trendingScore")[:5]
        lines = ["Product performance snapshot:"]
        for product in products:
            lines.append(
                f"- {product['name']}: {product['performance']} with trend score {product['trendingScore']} and {product['cartAdds']} cart adds."
            )
        return "\n".join(lines)

    def _product_snapshot(self, product: dict) -> str:
        offer = product["activeOffer"] if self._has_offer(product) else "No active offer"
        return (
            f"{product['name']} monitoring snapshot:\n"
            f"- Stock: {product['stock']} ({product['stockStatus']})\n"
            f"- Trend score: {product['trendingScore']}\n"
            f"- Views / cart adds: {product['views']} / {product['cartAdds']}\n"
            f"- Offer: {offer}\n"
            f"- Performance: {product['performance']}"
        )

    def _overview(self) -> str:
        top = max(self._data, key=lambda p: p.get("trendingScore", 0))
        low = [p for p in self._data if p.get("stockStatus") in {"Low Stock", "Critical Stock", "Out Of Stock"}]
        offers = [p for p in self._data if self._has_offer(p)]
        return (
            "Admin monitoring overview:\n"
            f"- Top trend: {top['name']} with score {top['trendingScore']}.\n"
            f"- Stock alerts: {len(low)} product(s) need attention.\n"
            f"- Active offers: {len(offers)} product(s) currently have offers.\n"
            "- Ask about trending products, low stock alerts, active offers, cart adds, views, or a specific product."
        )

    def _has_offer(self, product: dict) -> bool:
        offer = str(product.get("activeOffer") or "").lower()
        return offer not in {"", "none", "no offer", "no active offer"}
