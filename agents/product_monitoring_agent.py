import json
import os
from typing import Optional

from services.llm_service import LLMService


class ProductMonitoringAgent:
    """
    Smart Retail Product Monitoring Agent.
    Answers questions about stock, trending, performance, offers,
    cart activity, views, and low-stock alerts using a static
    monitoring dataset and the Groq LLM.
    """

    def __init__(self):
        self.llm_service = LLMService()
        self._data = self._load_monitoring_data()
        self._system_prompt = self._load_system_prompt()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_monitoring_data(self) -> list:
        data_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'product_monitoring_data.json'
        )
        data_path = os.path.normpath(data_path)
        try:
            with open(data_path, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

    def _load_system_prompt(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), '..', 'prompts', 'product_monitoring_prompt.txt'
        )
        prompt_path = os.path.normpath(prompt_path)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as fh:
                return fh.read().strip()
        except OSError:
            return "You are a Smart Retail Product Monitoring Agent."

    # ------------------------------------------------------------------
    # Helpers – pre-filter relevant products for common intents
    # ------------------------------------------------------------------

    def _trending_products(self, top_n: int = 5) -> list:
        return sorted(self._data, key=lambda p: p.get('trendingScore', 0), reverse=True)[:top_n]

    def _low_stock_products(self) -> list:
        return [p for p in self._data if p.get('stockStatus') in ('Low Stock', 'Critical Stock')]

    def _out_of_stock_products(self) -> list:
        return [p for p in self._data if p.get('stockStatus') == 'Out Of Stock']

    def _top_cart_products(self, top_n: int = 5) -> list:
        return sorted(self._data, key=lambda p: p.get('cartAdds', 0), reverse=True)[:top_n]

    def _active_offer_products(self) -> list:
        return [
            p for p in self._data
            if p.get('activeOffer') and p['activeOffer'].lower() not in ('no active offer', 'no offer')
        ]

    def _needs_attention(self) -> list:
        return [
            p for p in self._data
            if p.get('stockStatus') in ('Low Stock', 'Critical Stock', 'Out Of Stock')
            or p.get('performance') in ('Poor',)
        ]

    # ------------------------------------------------------------------
    # Build context string from monitoring data
    # ------------------------------------------------------------------

    def _build_context(self, user_message: str) -> str:
        lower = user_message.lower()

        # Decide which subset to highlight
        if any(kw in lower for kw in ['trending', 'trend', 'popular', 'top']):
            subset = self._trending_products()
            label = "Top Trending Products"
        elif any(kw in lower for kw in ['low stock', 'critical', 'attention', 'alert', 'need attention']):
            subset = self._needs_attention()
            label = "Products Needing Attention"
        elif any(kw in lower for kw in ['out of stock', 'unavailable', 'sold out']):
            subset = self._out_of_stock_products()
            label = "Out-of-Stock Products"
        elif any(kw in lower for kw in ['cart', 'added to cart', 'cart adds']):
            subset = self._top_cart_products()
            label = "Top Products by Cart Additions"
        elif any(kw in lower for kw in ['offer', 'discount', 'deal', 'coupon', 'promo']):
            subset = self._active_offer_products()
            label = "Products with Active Offers"
        elif any(kw in lower for kw in ['perform', 'best', 'top selling', 'top perform']):
            subset = sorted(self._data, key=lambda p: p.get('trendingScore', 0), reverse=True)
            label = "Product Performance Overview"
        elif any(kw in lower for kw in ['insight', 'overview', 'summary', 'monitor', 'status', 'report']):
            subset = self._data
            label = "Full Product Monitoring Dashboard"
        else:
            # Default: send all data so the LLM can pick what's relevant
            subset = self._data
            label = "Product Monitoring Data"

        lines = [f"--- {label} ---"]
        for p in subset:
            lines.append(
                f"• {p['name']} | Stock: {p['stock']} ({p['stockStatus']}) | "
                f"Trending: {p['trendingScore']} | Views: {p['views']} | "
                f"Cart Adds: {p['cartAdds']} | Offer: {p['activeOffer']} | "
                f"Performance: {p['performance']}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Main chat entry-point
    # ------------------------------------------------------------------

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        message = user_message.strip()
        if not message:
            return "Please ask me about product stock, trends, offers, or performance."

        if not self._data:
            return "No monitoring data available for this request."

        context = self._build_context(message)

        # Build a safe conversation history string to avoid f-string backslash issues
        convo_lines = []
        for m in self.llm_service.conversation_history[-5:]:
            convo_lines.append(f"User: {m.get('user','')}\\nAssistant: {m.get('assistant','')}")
        convo_text = chr(10).join(convo_lines)

        prompt = f"""{self._system_prompt}

    {context}

    Conversation history:
    {convo_text}

    Current admin question: {message}

    Respond naturally and concisely in 2-4 lines using only the monitoring data above."""

        fallback_lines = context.splitlines()[1:5]
        response = self.llm_service.invoke(
            prompt,
            fallback="Here are the matching monitoring results:\n" + "\n".join(fallback_lines),
        )

        # Track in shared conversation history
        self.llm_service.conversation_history.append(
            {"user": message, "assistant": response}
        )
        return response
