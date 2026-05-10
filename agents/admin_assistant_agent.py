from typing import Optional
from agents.product_monitoring_agent import ProductMonitoringAgent
from agents.analytics_prediction_agent import AnalyticsPredictionAgent
from services.langchain_orchestrator import AdminAgentOrchestrator

class AdminAssistantAgent:
    """
    Combined Admin Assistant Agent.
    Uses a simple LangChain runnable chain to route queries to either
    ProductMonitoringAgent or AnalyticsPredictionAgent.
    """
    def __init__(self):
        self.monitoring_agent = ProductMonitoringAgent()
        self.analytics_agent = AnalyticsPredictionAgent()
        self.orchestrator = AdminAgentOrchestrator(
            self.monitoring_agent.chat,
            self.analytics_agent.chat,
        )

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        lower_msg = user_message.lower()

        blocked_keywords = [
            'capital of', 'weather', 'news', 'prime minister', 'president',
            'cricket', 'football', 'bitcoin', 'stock market', 'recipe'
        ]
        if any(kw in lower_msg for kw in blocked_keywords):
            return (
                "I am here only for SmartRetailAI admin work: product monitoring, "
                "sales trends, demand prediction, restocking, offers, and inventory decisions."
            )

        return self.orchestrator.route(user_message, user_id)
