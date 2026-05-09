import json
import os
from typing import Optional

from services.llm_service import LLMService


class AnalyticsPredictionAgent:
    """Admin-only analytics and prediction answers grounded in project datasets."""

    def __init__(self):
        self.llm_service = LLMService()
        self._analytics = self._load_json("analytics_prediction_data.json")
        self._monitoring = self._load_json("product_monitoring_data.json")
        self._forecast = self._load_json("forecastData.json")

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
            return "Ask me about demand prediction, sales growth, restocking, offer impact, or product trend reasons."
        if not self._analytics:
            return "No analytics data available for this request."

        text = message.lower()
        if self._is_out_of_domain(text):
            return "I am here only for SmartRetailAI admin analytics: demand, growth, stock risk, restocking, and offer impact from app products."

        if any(word in text for word in ["high demand", "future demand", "predict", "forecast", "next month", "upcoming demand", "future sales"]):
            return self._humanise(message, self._future_demand())
        if any(word in text for word in ["restock", "shortage", "go out of stock", "stock risk", "reorder", "order more", "buy more stock", "need more stock"]):
            return self._humanise(message, self._restock_recommendations())
        if any(word in text for word in ["why", "reason", "increasing", "increase", "rising", "growth", "going up", "sales up"]):
            product = self._find_product(text)
            fallback = self._growth_reason(product) if product else self._growth_overview()
            return self._humanise(message, fallback)
        if any(word in text for word in ["offer", "discount", "campaign", "promotion", "working", "improve sales", "convert"]):
            return self._humanise(message, self._offer_impact())
        if any(word in text for word in ["decline", "declining", "decrease", "falling", "poor"]):
            return self._humanise(message, self._declining_products())
        if any(word in text for word in ["category", "segment"]):
            return self._humanise(message, self._category_insight())
        return self._humanise(message, self._analytics_overview())

    def _humanise(self, message: str, fallback: str) -> str:
        return self.llm_service.grounded_answer(
            message,
            fallback,
            "admin analytics and prediction assistant",
            fallback=fallback,
        )

    def _is_out_of_domain(self, text: str) -> bool:
        blocked = ["capital of", "weather", "news", "prime minister", "president", "cricket", "bitcoin", "recipe"]
        return any(word in text for word in blocked)

    def _find_product(self, text: str) -> Optional[dict]:
        for product in self._analytics:
            name = product.get("name", "").lower()
            name_tokens = [token for token in name.split() if len(token) > 3]
            if name and (name in text or any(token in text for token in name_tokens)):
                return product
        return None

    def _growth_value(self, product: dict) -> float:
        try:
            return float(str(product.get("salesGrowth", "0")).replace("%", "").replace("+", ""))
        except ValueError:
            return 0.0

    def _monitoring_by_name(self) -> dict[str, dict]:
        return {p.get("name", ""): p for p in self._monitoring}

    def _future_demand(self) -> str:
        products = sorted(self._analytics, key=self._growth_value, reverse=True)[:5]
        monitoring = self._monitoring_by_name()
        lines = ["Here is the demand picture I would act on:"]
        for product in products:
            stock = monitoring.get(product["name"], {}).get("stock", "N/A")
            lines.append(
                f"- {product['name']}: {product['salesGrowth']} growth. {product['futurePrediction']} Current stock: {stock}."
            )
        return "\n".join(lines)

    def _restock_recommendations(self) -> str:
        risk_terms = ["out of stock", "critical", "shortage", "recommended", "2 weeks"]
        stable_terms = ["no stock shortage", "current inventory sufficient", "currently healthy", "current stock sufficient"]
        products = [
            p for p in self._analytics
            if any(term in str(p.get("stockPrediction", "")).lower() for term in risk_terms)
            and not any(term in str(p.get("stockPrediction", "")).lower() for term in stable_terms)
        ]
        monitoring = self._monitoring_by_name()
        products.sort(key=lambda p: (monitoring.get(p["name"], {}).get("stock", 999), -self._growth_value(p)))
        lines = ["Here is the restock priority I would use:"]
        for product in products:
            live = monitoring.get(product["name"], {})
            lines.append(
                f"- {product['name']}: stock {live.get('stock', 'N/A')} ({live.get('stockStatus', 'N/A')}), "
                f"growth {product['salesGrowth']}. {product['stockPrediction']}"
            )
        return "\n".join(lines) if products else "No immediate restock risk is flagged in the analytics dataset."

    def _growth_reason(self, product: dict) -> str:
        monitoring = self._monitoring_by_name().get(product["name"], {})
        return (
            f"{product['name']} sales are {product['salesTrend'].lower()} ({product['salesGrowth']}) because {product['reason']}\n"
            f"- Future: {product['futurePrediction']}\n"
            f"- Stock forecast: {product['stockPrediction']}\n"
            f"- Engagement: trend score {monitoring.get('trendingScore', 'N/A')}, "
            f"{monitoring.get('views', 'N/A')} views, {monitoring.get('cartAdds', 'N/A')} cart adds."
        )

    def _growth_overview(self) -> str:
        products = sorted(self._analytics, key=self._growth_value, reverse=True)[:4]
        return "Here are the strongest growth signals:\n" + "\n".join(
            f"- {p['name']}: {p['salesGrowth']} growth from {p['reason']}"
            for p in products
        )

    def _offer_impact(self) -> str:
        monitoring = self._monitoring_by_name()
        products = []
        for product in self._analytics:
            offer = str(monitoring.get(product["name"], {}).get("activeOffer", ""))
            if offer.lower() not in {"", "none", "no offer", "no active offer"}:
                products.append((product, offer, monitoring.get(product["name"], {})))
        products.sort(key=lambda item: self._growth_value(item[0]), reverse=True)
        lines = ["Here are the offers that appear to be working best:"]
        for product, offer, live in products:
            lines.append(
                f"- {product['name']}: {offer}, {product['salesGrowth']} growth, "
                f"{live.get('cartAdds', 'N/A')} cart adds. Reason: {product['reason']}"
            )
        return "\n".join(lines)

    def _declining_products(self) -> str:
        products = [p for p in self._analytics if self._growth_value(p) < 0 or "declin" in str(p.get("salesTrend", "")).lower()]
        if not products:
            return "No declining product is flagged in the analytics dataset."
        return "Declining products:\n" + "\n".join(
            f"- {p['name']}: {p['salesGrowth']} growth. {p['reason']} {p['stockPrediction']}"
            for p in products
        )

    def _category_insight(self) -> str:
        category_map = {
            "Electronics": ["Wireless Headphones Pro", "Smart Watch Ultra", "Wireless Earbuds Air", "Phone"],
            "Fashion": ["Designer Sunglasses"],
            "Home & Kitchen": ["Premium Coffee Maker"],
            "Sports": ["Fitness Band Pro"],
            "Travel": ["Urban Travel Backpack"],
        }
        lookup = {p["name"]: p for p in self._analytics}
        lines = ["Category insight based on product growth:"]
        for category, names in category_map.items():
            products = [lookup[name] for name in names if name in lookup]
            if not products:
                continue
            avg_growth = sum(self._growth_value(p) for p in products) / len(products)
            top = max(products, key=self._growth_value)
            lines.append(f"- {category}: average growth {avg_growth:.1f}%, led by {top['name']} ({top['salesGrowth']}).")
        return "\n".join(lines)

    def _analytics_overview(self) -> str:
        top = max(self._analytics, key=self._growth_value)
        restock = self._restock_recommendations().splitlines()[1:4]
        return (
            "Admin analytics overview:\n"
            f"- Strongest growth: {top['name']} at {top['salesGrowth']}.\n"
            f"- Reason: {top['reason']}\n"
            "- Restock watch:\n" + "\n".join(restock)
        )
