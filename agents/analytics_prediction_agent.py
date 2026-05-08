import json
import os
from typing import Optional

from services.llm_service import LLMService


class AnalyticsPredictionAgent:
    """
    Smart Retail Analytics & Prediction Agent.
    Answers questions about sales trends, growth reasons, future demand
    predictions, stock forecasts, offer effectiveness, and business
    intelligence using a static analytics dataset and the Groq LLM.
    """

    def __init__(self):
        self.llm_service = LLMService()
        self._data = self._load_analytics_data()
        self._system_prompt = self._load_system_prompt()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_analytics_data(self) -> list:
        data_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'analytics_prediction_data.json'
        )
        data_path = os.path.normpath(data_path)
        try:
            with open(data_path, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

    def _load_system_prompt(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), '..', 'prompts', 'analytics_prediction_agent_prompt.txt'
        )
        prompt_path = os.path.normpath(prompt_path)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as fh:
                return fh.read().strip()
        except OSError:
            return "You are a Smart Retail Analytics & Prediction Agent."

    # ------------------------------------------------------------------
    # Helpers – pre-filter relevant products for common intents
    # ------------------------------------------------------------------

    def _high_growth_products(self, top_n: int = 5) -> list:
        """Products sorted by sales growth (highest first)."""
        def _growth_val(p):
            try:
                return float(p.get('salesGrowth', '0').replace('%', '').replace('+', ''))
            except (ValueError, AttributeError):
                return 0
        return sorted(self._data, key=_growth_val, reverse=True)[:top_n]

    def _declining_products(self) -> list:
        return [p for p in self._data if 'declin' in (p.get('salesTrend') or '').lower()]

    def _stock_risk_products(self) -> list:
        """Products whose stock predictions suggest shortages."""
        risk_keywords = ['out of stock', 'critical', 'shortage', 'restock', 'recommended']
        return [
            p for p in self._data
            if any(kw in (p.get('stockPrediction') or '').lower() for kw in risk_keywords)
        ]

    def _fast_growing_products(self) -> list:
        growth_keywords = ['rapid', 'strong', 'very high', 'high growth']
        return [
            p for p in self._data
            if any(kw in (p.get('salesTrend') or '').lower() for kw in growth_keywords)
        ]

    # ------------------------------------------------------------------
    # Build context string from analytics data
    # ------------------------------------------------------------------

    def _build_context(self, user_message: str) -> str:
        lower = user_message.lower()

        # Intent-based subset selection
        if any(kw in lower for kw in ['declining', 'decrease', 'drop', 'falling', 'poor']):
            subset = self._declining_products() or self._data
            label = "Declining Products Analytics"
        elif any(kw in lower for kw in ['restock', 'shortage', 'out of stock', 'stock risk', 'stock prediction']):
            subset = self._stock_risk_products() or self._data
            label = "Stock Risk & Restock Recommendations"
        elif any(kw in lower for kw in ['promote', 'marketing', 'campaign', 'offer', 'discount', 'effectiveness']):
            subset = self._data
            label = "Offer & Promotion Analytics"
        elif any(kw in lower for kw in ['growth', 'growing', 'increase', 'rising', 'top', 'best', 'high demand']):
            subset = self._high_growth_products()
            label = "High-Growth Products Analytics"
        elif any(kw in lower for kw in ['predict', 'forecast', 'future', 'next month', 'expect', 'demand']):
            subset = self._data
            label = "Future Demand Predictions"
        elif any(kw in lower for kw in ['why', 'reason', 'cause', 'explain']):
            subset = self._data
            label = "Sales Trend Analysis & Reasons"
        elif any(kw in lower for kw in ['trend', 'sales', 'performance', 'category']):
            subset = self._data
            label = "Sales Trends Overview"
        elif any(kw in lower for kw in ['insight', 'overview', 'summary', 'report', 'analytics']):
            subset = self._data
            label = "Full Analytics & Prediction Report"
        else:
            subset = self._data
            label = "Analytics & Prediction Data"

        lines = [f"--- {label} ---"]
        for p in subset:
            lines.append(
                f"• {p['name']} | Trend: {p.get('salesTrend', 'N/A')} | "
                f"Growth: {p.get('salesGrowth', 'N/A')} | "
                f"Reason: {p.get('reason', 'N/A')} | "
                f"Future: {p.get('futurePrediction', 'N/A')} | "
                f"Stock Forecast: {p.get('stockPrediction', 'N/A')}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Main chat entry-point
    # ------------------------------------------------------------------

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        message = user_message.strip()
        if not message:
            return "Please ask me about sales trends, predictions, growth analysis, or restocking recommendations."

        if not self._data:
            return "No analytics data available for this request."

        context = self._build_context(message)

        convo_lines = []
        for m in self.llm_service.conversation_history[-5:]:
            convo_lines.append(f"User: {m.get('user','')}\\nAssistant: {m.get('assistant','')}")
        convo_text = chr(10).join(convo_lines)

        prompt = f"""{self._system_prompt}

    {context}

    Conversation history:
    {convo_text}

    Current admin question: {message}

    Respond naturally and concisely in 2-4 lines using only the analytics data above."""

        fallback_lines = context.splitlines()[1:5]
        response = self.llm_service.invoke(
            prompt,
            fallback="Here are the matching analytics results:\n" + "\n".join(fallback_lines),
        )

        # Track in shared conversation history
        self.llm_service.conversation_history.append(
            {"user": message, "assistant": response}
        )
        return response
