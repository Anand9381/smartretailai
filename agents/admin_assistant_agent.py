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

        blocked_keywords = [
            'capital of', 'weather', 'news', 'prime minister', 'president',
            'cricket', 'football', 'bitcoin', 'stock market', 'recipe'
        ]
        if any(kw in lower_msg for kw in blocked_keywords):
            return (
                "I am here only for SmartRetailAI admin work: product monitoring, "
                "sales trends, demand prediction, restocking, offers, and inventory decisions."
            )
        
        monitoring_keywords = [
            'which products are trending', 'trending products', 'low stock alert',
            'low stock alerts', 'active offers', 'highest cart adds', 'cart adds',
            'views', 'out of stock', 'stock alerts', 'product monitoring',
            'popular', 'most viewed', 'most added', 'current stock', 'stock level',
            'stock levels', 'available stock', 'running low', 'almost over',
            'nearly finished', 'selling fast', 'top product', 'best product',
            'offers running', 'discounts running', 'deals running'
        ]
        if any(kw in lower_msg for kw in monitoring_keywords):
            return self.monitoring_agent.chat(user_message, user_id)

        # Keywords that strongly indicate analytics/prediction intent
        analytics_keywords = [
            'predict', 'forecast', 'future', 'trend', 'growth', 'decline',
            'why', 'reason', 'cause', 'explain', 'insight', 'next month', 'expected',
            'high demand', 'restock', 'shortage', 'sales increasing', 'demand',
            'improve sales', 'offer impact', 'promotion impact', 'reorder',
            'order more', 'buy more stock', 'need more stock', 'future sales',
            'upcoming demand', 'going up', 'increasing sales', 'growth reason',
            'campaign', 'working best', 'which offer works', 'conversions'
        ]
        
        # If any analytics keyword is present, route to AnalyticsPredictionAgent
        if any(kw in lower_msg for kw in analytics_keywords):
            return self.analytics_agent.chat(user_message, user_id)
        
        # Otherwise, default to ProductMonitoringAgent
        return self.monitoring_agent.chat(user_message, user_id)
