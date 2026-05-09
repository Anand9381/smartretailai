"""Shared MongoDB connection and collection handles."""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import certifi

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_retail")

mongo_client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000,
    tlsCAFile=certifi.where() if MONGO_URI.startswith("mongodb+srv://") else None,
)
mongo_db = mongo_client[DB_NAME]

users_collection: Collection[Dict[str, Any]] = mongo_db["users"]
products_collection: Collection[Dict[str, Any]] = mongo_db["products"]
orders_collection: Collection[Dict[str, Any]] = mongo_db["orders"]
carts_collection: Collection[Dict[str, Any]] = mongo_db["carts"]
retail_analytics_collection: Collection[Dict[str, Any]] = mongo_db["retail_analytics"]
chat_logs_collection: Collection[Dict[str, Any]] = mongo_db["chat_logs"]
documents_collection: Collection[Dict[str, Any]] = mongo_db["documents"]
sales_collection: Collection[Dict[str, Any]] = mongo_db["sales"]

print(f"[db.py] MongoDB database={mongo_db.name}, uri={MONGO_URI.split('@')[-1]}")


def test_connection() -> bool:
    """Return True when MongoDB responds to a ping."""
    try:
        mongo_client.admin.command("ping")
        return True
    except PyMongoError as exc:
        raise RuntimeError(f"MongoDB connection test failed: {exc}") from exc


if __name__ == "__main__":
    try:
        print("Testing MongoDB connection...")
        print("Connection OK:", test_connection())
    except Exception as exc:  # pragma: no cover
        print("Connection test failed:", exc)
