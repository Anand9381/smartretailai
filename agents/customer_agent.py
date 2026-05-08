import re
from datetime import datetime
from typing import Optional

from services.llm_service import LLMService
from services.cosmos_service import CosmosService
from services.azure_search_service import AzureSearchService

class CustomerAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.cosmos_service = CosmosService()
        self.azure_search = AzureSearchService()

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        message = user_message.strip()
        if not message:
            return "Please tell me what you are looking for, and I will fetch live product or order details for you."

        lower_text = message.lower()

        if self._is_order_question(lower_text) and user_id:
            if self._is_list_orders_query(lower_text):
                return self._answer_order_list(user_id)
            if self._is_order_status_query(lower_text):
                return self._answer_order_status(user_id)
            return self._answer_order_list(user_id)

        if self._is_product_question(lower_text):
            if self._is_list_products_query(lower_text):
                return self._answer_list_products()
            return self._answer_product_question(message, lower_text)

        if self._is_faq_question(lower_text):
            return self._answer_faq_question(message)

        return self._fallback_answer(message)

    def _is_order_question(self, text: str) -> bool:
        return any(keyword in text for keyword in ["order", "track", "status", "delivery", "shipping"])

    def _is_list_orders_query(self, text: str) -> bool:
        return any(phrase in text for phrase in [
            "list my orders",
            "show my orders",
            "latest orders",
            "recent orders",
            "order history",
            "my orders",
            "last orders",
        ])

    def _is_order_status_query(self, text: str) -> bool:
        return any(keyword in text for keyword in ["status", "track", "delivery", "shipment"])

    def _is_product_question(self, text: str) -> bool:
        return any(keyword in text for keyword in [
            "product",
            "price",
            "stock",
            "available",
            "show",
            "find",
            "search",
            "under",
            "category",
            "buy",
            "discount",
            "deal",
            "coupon",
            "offer",
            "electronics",
            "mobile",
            "laptop",
            "tv",
            "smartphone",
            "list",
            "catalog",
        ])

    def _is_list_products_query(self, text: str) -> bool:
        # Check if it's a simple list request without price/category filters
        has_qualifier = any(word in text for word in ["under", "below", "above", "price", "category", "brand", "electronics", "fashion", "sports", "travel", "kitchen"])
        if has_qualifier:
            return False
        
        return any(phrase in text for phrase in [
            "list products",
            "show all products",
            "all products",
            "product catalog",
            "browse products",
            "view products",
            "available products",
        ])

    def _is_faq_question(self, text: str) -> bool:
        return any(keyword in text for keyword in ["return", "warranty", "shipping", "policy", "refund", "cancel"])

    def _parse_price(self, text: str) -> Optional[int]:
        patterns = [
            r"(?:under|below|less than|up to|upto|max)\s+₹?\s*([0-9,]+)",
            r"(?:under|below|less than|up to|upto|max)\s*₹?\s*([0-9,]+)",
            r"₹\s*([0-9,]+)",
            r"\$\s*([0-9,]+)",
            r"(?:price|cost).*?([0-9,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1).replace(",", ""))
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_product_query(self, text: str) -> str:
        cleaned = re.sub(
            r"\b(tell|me|about|show|find|search|products?|product|buy|want|looking for|recommend|discount|deal|coupon|offer|for|in|with|under|below|less than|up to|upto|max|₹|rs|rupees)\b",
            "",
            text,
        )
        return re.sub(r"[^a-z0-9 ]", " ", cleaned).strip()

    def _answer_list_products(self) -> str:
        all_products = self.cosmos_service.get_products(limit=100)
        if not all_products:
            return "No products available at the moment."
        
        titles = [p.get('name', 'Unnamed') for p in all_products]
        return "Available Products:\n• " + "\n• ".join(titles)

    def _answer_product_question(self, message: str, lower_text: str) -> str:
        price = self._parse_price(lower_text)
        products = []

        if price is not None and any(keyword in lower_text for keyword in ["under", "below", "less than", "up to", "upto", "max"]):
            products = self.cosmos_service.search_products_by_price(price)

        if not products:
            query = self._extract_product_query(lower_text)
            products = self.cosmos_service.get_products(query or message, limit=5)

        if not products:
            products = self.cosmos_service.get_products(limit=5)

        if not products:
            return "I could not find matching products in the Cosmos DB catalog. Try another category, brand, or price range."

        context_lines = ["Products found in catalog:"]
        for product in products[:3]:
            name = product.get('name', 'Unnamed product')
            price_val = product.get('price', 'N/A')
            stock = product.get('stock', 0)
            category = product.get('category', 'General')
            desc = product.get('desc', '')
            badge = product.get('badge', '')
            
            stock_text = f"{stock} in stock" if stock > 0 else "Out of stock"
            context_lines.append(
                "Catalog product record from live MongoDB:\n"
                f"Name: {name}\n"
                f"Category: {category}\n"
                f"Price: ${price_val}\n"
                f"Stock: {stock_text}\n"
                f"Badge: {badge}\n"
                f"Description: {desc}"
            )

        context = "\n\n".join(context_lines)
        return self.llm_service.chat(message, context=context)

    def _answer_order_list(self, user_id: str) -> str:
        orders = self.cosmos_service.get_user_orders(user_id)
        if not orders:
            return "I don't see any orders for your account right now. Place an order and I will show it here immediately."

        sorted_orders = self._sort_orders(orders)
        lines = []
        for index, order in enumerate(sorted_orders[:3], start=1):
            ref = order.get("order_number") or str(order.get("_id", "unknown"))
            status = order.get("status", "Processing")
            total = order.get("total") or order.get("amount") or order.get("grand_total") or 0
            items = order.get("items", [])
            item_count = len(items) if isinstance(items, list) else order.get("count", 0)
            date_text = self._format_order_date(order)
            lines.append(f"{index}. {ref} — ${total}, {item_count} items, {status}, {date_text}")

        return "Here are your most recent orders:\n" + "\n".join(lines)

    def _answer_order_status(self, user_id: str) -> str:
        latest = self._get_latest_order(user_id)
        if not latest:
            return "I don't see any orders for your account right now. Place an order and I will track it for you."

        ref = latest.get("order_number") or str(latest.get("_id", "unknown"))
        status = latest.get("status", "Processing")
        total = latest.get("total") or latest.get("amount") or latest.get("grand_total") or 0
        items = latest.get("items", [])
        item_count = len(items) if isinstance(items, list) else latest.get("count", 0)
        date_text = self._format_order_date(latest)

        return (
            f"Your latest order {ref} is currently {status}. "
            f"It was placed on {date_text}, contains {item_count} items, and totals ${total}."
        )

    def _sort_orders(self, orders):
        def _to_timestamp(order):
            # normalize various date formats to a float timestamp for safe sorting
            val = order.get("order_date") or order.get("created_at") or order.get("date") or ""
            if isinstance(val, datetime):
                try:
                    return val.timestamp()
                except Exception:
                    return 0.0
            if isinstance(val, (int, float)):
                try:
                    return float(val)
                except Exception:
                    return 0.0
            if isinstance(val, str):
                try:
                    # handle ISO format strings (possibly with fractional seconds)
                    dt = datetime.fromisoformat(val.split(".")[0])
                    return dt.timestamp()
                except Exception:
                    # fallback: empty or unparseable string
                    return 0.0
            return 0.0

        return sorted(orders, key=_to_timestamp, reverse=True)

    def _get_latest_order(self, user_id: str):
        orders = self.cosmos_service.get_user_orders(user_id)
        sorted_orders = self._sort_orders(orders)
        return sorted_orders[0] if sorted_orders else None

    def _format_order_date(self, order):
        date_value = order.get("order_date") or order.get("created_at") or ""
        if isinstance(date_value, (int, float)):
            try:
                return datetime.fromtimestamp(int(date_value)).strftime("%Y-%m-%d")
            except OSError:
                return str(date_value)
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.split(".")[0]).strftime("%Y-%m-%d")
            except ValueError:
                return date_value
        return str(date_value)

    def _answer_faq_question(self, message: str) -> str:
        snippets = self.azure_search.build_context(message, top=2)
        context = "\n".join(snippets) if snippets else ""
        return self.llm_service.chat(message, context=context)

    def _fallback_answer(self, message: str) -> str:
        snippets = self.azure_search.build_context(message, top=2)
        context = "\n".join(snippets) if snippets else ""
        return self.llm_service.chat(message, context=context)
