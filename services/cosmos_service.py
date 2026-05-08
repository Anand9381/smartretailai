from db import products_collection, orders_collection, users_collection
from typing import List, Dict, Any
from bson import ObjectId

class CosmosService:
    def get_products(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Get products from Cosmos DB, optionally filtered by query."""
        # Simple text search on name, category or description
        if query:
            regex = {"$regex": query, "$options": "i"}
            products = list(products_collection.find({
                "$or": [
                    {"name": regex},
                    {"category": regex},
                    {"desc": regex}
                ]
            }).limit(limit))
        else:
            products = list(products_collection.find().limit(limit))
        return products

    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Get a single product by ID."""
        return products_collection.find_one({"_id": product_id})

    def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        """Get orders for a specific user."""
        # Orders in the database may store `user_id` either as a string or as an ObjectId.
        # Query for both forms when possible for robust results.
        try:
            if user_id and ObjectId.is_valid(user_id):
                obj = ObjectId(user_id)
                query = {"$or": [{"user_id": user_id}, {"user_id": obj}]}
            else:
                query = {"user_id": user_id}
        except Exception:
            query = {"user_id": user_id}
        return list(orders_collection.find(query))

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        # Accept either string id or ObjectId
        try:
            if user_id and ObjectId.is_valid(user_id):
                return users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            pass
        return users_collection.find_one({"_id": user_id})

    def search_products_by_price(self, max_price: float) -> List[Dict[str, Any]]:
        """Get products under a certain price."""
        return list(products_collection.find({"price": {"$lte": max_price}}))

    def get_product_stock(self, product_id: str) -> int:
        """Get stock for a product."""
        product = self.get_product_by_id(product_id)
        return product.get("stock", 0) if product else 0