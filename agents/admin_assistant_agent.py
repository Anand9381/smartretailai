from typing import Optional
from agents.product_monitoring_agent import ProductMonitoringAgent
from agents.analytics_prediction_agent import AnalyticsPredictionAgent

class AdminAssistantAgent:
    """
    Combined Admin Assistant Agent.
    Routes queries to either ProductMonitoringAgent or AnalyticsPredictionAgent
    based on keywords in the user message.
    """
    def __init__(self):
        self.monitoring_agent = ProductMonitoringAgent()
        self.analytics_agent = AnalyticsPredictionAgent()

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        lower_msg = user_message.lower()
        
        # Keywords that strongly indicate analytics/prediction intent
        analytics_keywords = [
            'predict', 'forecast', 'future', 'trend', 'growth', 'decline',
            'why', 'reason', 'cause', 'explain', 'insight', 'next month', 'expected'
        ]
        
        # If any analytics keyword is present, route to AnalyticsPredictionAgent
        if any(kw in lower_msg for kw in analytics_keywords):
            return self.analytics_agent.chat(user_message, user_id)
        
        # Otherwise, default to ProductMonitoringAgent
        return self.monitoring_agent.chat(user_message, user_id)
