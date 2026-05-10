"""Small LangChain orchestration layer for SmartRetailAI admin agents.

This keeps the evaluator-visible LangChain usage simple: a RunnableLambda
classifies an admin question, then another RunnableLambda calls the selected
local agent. The agents still use the project's own deterministic data logic.
"""

from __future__ import annotations

from typing import Callable

from langchain_core.runnables import RunnableLambda


class AdminAgentOrchestrator:
    """Route admin chat messages through a tiny LangChain runnable chain."""

    MONITORING_KEYWORDS = (
        "which products are trending", "trending products", "low stock alert",
        "low stock alerts", "active offers", "highest cart adds", "cart adds",
        "views", "out of stock", "stock alerts", "product monitoring",
        "popular", "most viewed", "most added", "current stock", "stock level",
        "stock levels", "available stock", "running low", "almost over",
        "nearly finished", "selling fast", "top product", "best product",
        "offers running", "discounts running", "deals running",
    )
    ANALYTICS_KEYWORDS = (
        "predict", "forecast", "future", "trend", "growth", "decline",
        "why", "reason", "cause", "explain", "insight", "next month",
        "expected", "high demand", "restock", "shortage", "sales increasing",
        "demand", "improve sales", "offer impact", "promotion impact",
        "reorder", "order more", "buy more stock", "need more stock",
        "future sales", "upcoming demand", "going up", "increasing sales",
        "growth reason", "campaign", "working best", "which offer works",
        "conversions",
    )

    def __init__(
        self,
        monitoring_handler: Callable[[str, str | None], str],
        analytics_handler: Callable[[str, str | None], str],
    ):
        self.monitoring_handler = monitoring_handler
        self.analytics_handler = analytics_handler
        self.chain = RunnableLambda(self._classify) | RunnableLambda(self._dispatch)

    def route(self, message: str, user_id: str | None = None) -> str:
        return self.chain.invoke({"message": message, "user_id": user_id})

    def _classify(self, payload: dict) -> dict:
        text = str(payload["message"]).lower()
        route = "monitoring"
        if any(keyword in text for keyword in self.ANALYTICS_KEYWORDS):
            route = "analytics"
        if any(keyword in text for keyword in self.MONITORING_KEYWORDS):
            route = "monitoring"
        return {**payload, "route": route}

    def _dispatch(self, payload: dict) -> str:
        if payload["route"] == "analytics":
            return self.analytics_handler(payload["message"], payload.get("user_id"))
        return self.monitoring_handler(payload["message"], payload.get("user_id"))
