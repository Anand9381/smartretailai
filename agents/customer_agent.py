import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.llm_service import LLMService
from services.mongo_service import MongoService


class CustomerAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.mongo_service = MongoService()
        self.project_root = Path(__file__).resolve().parents[1]
        self.products_seed_path = self.project_root / "data" / "products_seed.json"
        self.policy_files = {
            "returns": self.project_root / "documents" / "return_policy.md",
            "shipping": self.project_root / "documents" / "shipping_policy.md",
            "warranty": self.project_root / "documents" / "warranty_rules.md",
            "promotions": self.project_root / "documents" / "promotions_discounts.md",
        }

    def chat(self, user_message: str, user_id: Optional[str] = None) -> str:
        message = user_message.strip()
        if not message:
            return "Tell me what you are looking for: a product, price range, offer, shipping, return, or warranty question."

        lower_text = message.lower()

        if self._is_admin_or_unrelated_question(lower_text):
            return (
                "I can help with shopping questions only: products, prices, stock, offers, orders, shipping, returns, and warranty. "
                "Admin analytics like sales, revenue, forecasts, and restocking are available only in the admin assistant."
            )

        if self._is_order_question(lower_text):
            if not user_id:
                return "Please sign in as a customer and I can check your own order details."
            if self._is_order_status_query(lower_text):
                return self._answer_order_status(user_id)
            return self._answer_order_list(user_id)

        is_policy_question = self._is_policy_question(lower_text)
        is_product_question = self._is_product_question(lower_text)
        is_product_offer_question = is_product_question and any(
            keyword in lower_text for keyword in ["discount", "offer", "deal", "sale"]
        )

        if is_policy_question and not is_product_offer_question:
            return self._answer_policy_question(message, lower_text)

        if is_product_question:
            return self._answer_product_question(message, lower_text)

        if is_policy_question:
            return self._answer_policy_question(message, lower_text)

        return (
            "I am here for SmartRetailAI shopping help. Ask me about products, prices, stock, offers, returns, shipping, warranty, or your orders."
        )

    def _is_admin_or_unrelated_question(self, text: str) -> bool:
        admin_keywords = [
            "total sales", "revenue", "profit", "analytics", "forecast", "prediction",
            "demand", "restock", "restocking", "business insight", "sales growth",
            "top performing", "performance", "low stock alert", "low stock alerts",
            "inventory report", "customer count", "orders count", "power bi",
        ]
        unrelated_keywords = [
            "capital of", "prime minister", "president", "weather", "temperature",
            "news", "current affairs", "stock market", "bitcoin", "cricket score",
            "football score", "time in", "date today",
        ]
        return any(keyword in text for keyword in admin_keywords + unrelated_keywords)

    def _is_order_question(self, text: str) -> bool:
        return any(keyword in text for keyword in ["my order", "my orders", "track", "order status", "delivery status"])

    def _is_order_status_query(self, text: str) -> bool:
        return any(keyword in text for keyword in ["status", "track", "delivery"])

    def _is_policy_question(self, text: str) -> bool:
        return any(keyword in text for keyword in [
            "return", "refund", "exchange", "shipping", "delivery", "warranty",
            "support", "coupon", "discount", "offer", "promotion", "cod",
            "cancel", "cancellation", "replacement",
        ])

    def _is_product_question(self, text: str) -> bool:
        product_names = [p["name"].lower() for p in self._get_products()]
        return any(name in text for name in product_names) or any(keyword in text for keyword in [
            "product", "products", "price", "stock", "available", "show", "find",
            "search", "under", "below", "above", "category", "buy", "catalog",
            "electronics", "fashion", "sports", "travel", "kitchen", "home",
            "headphone", "watch", "sunglass", "coffee", "earbud", "fitness",
            "backpack", "phone", "cheapest", "least price", "lowest price",
            "expensive", "highest price", "out of stock", "in stock",
        ])

    def _get_products(self) -> list[dict]:
        try:
            products = self.mongo_service.get_products(limit=200)
        except Exception:
            products = []
        if products:
            return [self._clean_product(product) for product in products]

        try:
            return [self._clean_product(product) for product in json.loads(self.products_seed_path.read_text(encoding="utf-8"))]
        except Exception:
            return []

    def _clean_product(self, product: dict) -> dict:
        return {
            "slug": str(product.get("slug") or ""),
            "name": str(product.get("name") or "Unnamed product"),
            "category": str(product.get("category") or "General"),
            "price": float(product.get("price") or 0),
            "stock": int(product.get("stock") or 0),
            "badge": str(product.get("badge") or ""),
            "desc": str(product.get("desc") or ""),
        }

    def _answer_product_question(self, message: str, lower_text: str) -> str:
        products = self._select_products(lower_text)
        if not products:
            return "I could not find that in the catalog. Try a product name, category, or price range like 'electronics under 200'."

        if self._wants_single_best(lower_text):
            product = products[0]
            fallback = self._format_single_product(product, "Here is the best match I found:")
            return self._humanise_customer_answer(message, fallback)

        if self._wants_comparison(lower_text) and len(products) > 1:
            fallback = self._format_product_list(products[:6], "Here are the matching products:")
            return self._humanise_customer_answer(message, fallback)

        if len(products) == 1 or self._mentions_specific_product(lower_text):
            fallback = self._format_single_product(products[0], "Sure, here are the details:")
            return self._humanise_customer_answer(message, fallback)

        fallback = self._format_product_list(products[:8], "Here are the products I found:")
        return self._humanise_customer_answer(message, fallback)

    def _select_products(self, text: str) -> list[dict]:
        products = self._get_products()
        if not products:
            return []

        category = self._extract_category(text)
        if category:
            products = [p for p in products if category in p["category"].lower()]

        max_price = self._parse_price(text, ["under", "below", "less than", "up to", "upto", "max"])
        min_price = self._parse_price(text, ["above", "over", "greater than", "more than", "min"])
        if max_price is not None:
            products = [p for p in products if p["price"] <= max_price]
        if min_price is not None:
            products = [p for p in products if p["price"] >= min_price]

        if "out of stock" in text:
            products = [p for p in products if p["stock"] <= 0]
        elif "in stock" in text or "available" in text:
            products = [p for p in products if p["stock"] > 0]

        matches = self._match_named_products(text, products)
        if matches:
            products = matches

        if any(keyword in text for keyword in ["cheapest", "least price", "lowest price", "low price", "budget"]):
            return sorted(products, key=lambda p: p["price"])
        if any(keyword in text for keyword in ["highest price", "expensive", "costliest", "premium"]):
            return sorted(products, key=lambda p: p["price"], reverse=True)
        if any(keyword in text for keyword in ["offer", "discount", "coupon", "deal", "sale"]):
            offer_products = [p for p in products if self._has_offer_signal(p)]
            return offer_products or products
        if category or max_price is not None or min_price is not None:
            return sorted(products, key=lambda p: (p["stock"] <= 0, p["price"]))
        return sorted(products, key=lambda p: (p["stock"] <= 0, p["category"], p["price"]))

    def _extract_category(self, text: str) -> Optional[str]:
        categories = {
            "electronics": ["electronics", "gadget", "gadgets", "tech"],
            "fashion": ["fashion", "sunglasses", "shades"],
            "home & kitchen": ["home", "kitchen", "coffee"],
            "sports": ["sports", "fitness"],
            "travel": ["travel", "backpack", "bag"],
        }
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        return None

    def _parse_price(self, text: str, markers: list[str]) -> Optional[float]:
        marker_pattern = "|".join(re.escape(marker) for marker in markers)
        patterns = [
            rf"(?:{marker_pattern})\s+(?:rs\.?|inr|\$)?\s*([0-9,]+(?:\.[0-9]+)?)",
            rf"(?:rs\.?|inr|\$)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:{marker_pattern})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except ValueError:
                    return None
        return None

    def _match_named_products(self, text: str, products: list[dict]) -> list[dict]:
        exact_matches = [
            product for product in products
            if self._phrase_in_text(product["name"].lower(), text) or self._phrase_in_text(product["slug"].replace("-", " "), text)
        ]
        if exact_matches:
            return exact_matches

        stopwords = {
            "show", "tell", "about", "product", "products", "price", "stock", "details",
            "description", "explain", "find", "search", "buy", "available", "under",
            "below", "above", "discount", "offer", "deal", "category", "best",
            "electronics", "fashion", "sports", "travel", "kitchen", "home", "all",
            "list", "which", "what", "with", "left", "inr", "rs",
        }
        query_tokens = {
            token for token in re.findall(r"[a-z0-9]+", text)
            if token not in stopwords and not token.isdigit() and len(token) > 2
        }
        if not query_tokens:
            return []

        scored = []
        for product in products:
            name_haystack = f"{product['name']} {product['slug']}".lower()
            detail_haystack = f"{product['desc']} {product['badge']}".lower()
            score = sum(3 for token in query_tokens if token in name_haystack)
            score += sum(1 for token in query_tokens if token in detail_haystack)
            if score:
                scored.append((score, product))
        scored.sort(key=lambda item: (-item[0], item[1]["price"]))
        return [product for _, product in scored]

    def _phrase_in_text(self, phrase: str, text: str) -> bool:
        escaped = re.escape(phrase.strip())
        return bool(escaped and re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text))

    def _wants_single_best(self, text: str) -> bool:
        return any(keyword in text for keyword in ["cheapest", "least price", "lowest price", "highest price", "expensive", "costliest"])

    def _wants_comparison(self, text: str) -> bool:
        return any(keyword in text for keyword in ["compare", "list", "show", "all", "which", "under", "below", "above", "category"])

    def _mentions_specific_product(self, text: str) -> bool:
        return bool(self._match_named_products(text, self._get_products()))

    def _has_offer_signal(self, product: dict) -> bool:
        text = f"{product['badge']} {product['desc']}".lower()
        return any(keyword in text for keyword in ["discount", "off", "coupon", "sale", "bundle", "free shipping"])

    def _format_single_product(self, product: dict, intro: str) -> str:
        stock_text = f"{product['stock']} in stock" if product["stock"] > 0 else "Out of stock"
        return (
            f"{intro}\n"
            f"- {product['name']} ({product['category']})\n"
            f"- Price: ${product['price']:.2f}\n"
            f"- Stock: {stock_text}\n"
            f"- Description: {product['desc']}"
        )

    def _format_product_list(self, products: list[dict], intro: str) -> str:
        lines = [intro]
        for product in products:
            stock_text = f"{product['stock']} left" if product["stock"] > 0 else "Out of stock"
            badge = f" - {product['badge']}" if product["badge"] else ""
            lines.append(
                f"- {product['name']}: current catalog price ${product['price']:.2f}, "
                f"{stock_text}, {product['category']}{badge}. Description: {product['desc']}"
            )
        return "\n".join(lines)

    def _humanise_customer_answer(self, message: str, fallback: str) -> str:
        facts = (
            "Important product rule: the Price line is the current catalog price. "
            "Do not infer original price, final discounted price, or extra offers.\n"
            f"{fallback}"
        )
        return self.llm_service.grounded_answer(
            message,
            facts,
            "customer shopping assistant",
            fallback=fallback,
        )

    def _answer_policy_question(self, message: str, lower_text: str) -> str:
        selected = self._select_policy_files(lower_text)
        context = "\n\n".join(self._read_policy_file(name) for name in selected).strip()
        if not context:
            return "I can help with returns, refunds, shipping, warranty, and discounts, but I could not load the policy file right now."

        fallback = self._policy_fallback(lower_text, context)
        facts = (
            "Policy rule: answer only from these SmartRetailAI policy documents. "
            "Do not add outside legal, courier, or marketplace policy details.\n"
            f"{context[:5000]}"
        )
        return self.llm_service.grounded_answer(
            message,
            facts,
            "customer policy assistant",
            fallback=fallback,
        )

    def _select_policy_files(self, text: str) -> list[str]:
        selected = []
        if any(word in text for word in ["return", "refund", "exchange", "cancel", "cancellation", "replacement"]):
            selected.append("returns")
        if any(word in text for word in ["shipping", "delivery", "deliver", "cod", "package"]):
            selected.append("shipping")
        if any(word in text for word in ["warranty", "support", "repair", "service"]):
            selected.append("warranty")
        if any(word in text for word in ["coupon", "discount", "offer", "promotion", "deal", "loyalty"]):
            selected.append("promotions")
        return selected or ["returns", "shipping", "warranty", "promotions"]

    def _read_policy_file(self, name: str) -> str:
        try:
            return self.policy_files[name].read_text(encoding="utf-8")
        except OSError:
            return ""

    def _policy_fallback(self, text: str, context: str) -> str:
        lines = []
        for raw_line in context.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            clean = re.sub(r"^\d+\.\s*", "- ", line)
            if clean.startswith("- ") or clean.startswith("**"):
                lines.append(clean)
        return "Here is the policy information I found:\n" + "\n".join(lines[:6])

    def _answer_order_list(self, user_id: str) -> str:
        orders = self.mongo_service.get_user_orders(user_id)
        if not orders:
            return "I do not see any orders for your account yet. Once you place an order, I can show it here."

        sorted_orders = self._sort_orders(orders)
        lines = ["Here are your recent orders:"]
        for index, order in enumerate(sorted_orders[:3], start=1):
            ref = order.get("order_number") or order.get("order_code") or str(order.get("_id", "unknown"))
            status = str(order.get("status", "Processing")).title()
            total = order.get("total") or order.get("amount") or order.get("grand_total") or 0
            item_count = len(order.get("items", [])) if isinstance(order.get("items"), list) else order.get("count", 0)
            lines.append(f"- {index}. {ref}: ${float(total):.2f}, {item_count} item(s), {status}, {self._format_order_date(order)}")
        fallback = "\n".join(lines)
        return self._humanise_customer_answer("my orders", fallback)

    def _answer_order_status(self, user_id: str) -> str:
        latest = self._get_latest_order(user_id)
        if not latest:
            return "I do not see any orders for your account yet. Place an order and I can help track it."

        ref = latest.get("order_number") or latest.get("order_code") or str(latest.get("_id", "unknown"))
        status = str(latest.get("status", "Processing")).title()
        total = latest.get("total") or latest.get("amount") or latest.get("grand_total") or 0
        fallback = f"Your latest order {ref} is {status}. It was placed on {self._format_order_date(latest)} and totals ${float(total):.2f}."
        return self._humanise_customer_answer("order status", fallback)

    def _sort_orders(self, orders):
        def _to_timestamp(order):
            value = order.get("order_date") or order.get("created_at") or order.get("date") or ""
            if isinstance(value, datetime):
                return value.timestamp()
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.split(".")[0]).timestamp()
                except ValueError:
                    return 0.0
            return 0.0

        return sorted(orders, key=_to_timestamp, reverse=True)

    def _get_latest_order(self, user_id: str):
        orders = self.mongo_service.get_user_orders(user_id)
        sorted_orders = self._sort_orders(orders)
        return sorted_orders[0] if sorted_orders else None

    def _format_order_date(self, order):
        value = order.get("order_date") or order.get("created_at") or order.get("date") or ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d")
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.split(".")[0]).strftime("%Y-%m-%d")
            except ValueError:
                return value or "date not available"
        return "date not available"
