"""Shared database connection helpers.

Prefer local MongoDB when available. Cosmos DB is optional — if
`COSMOS_DB_URI` is set we will attempt to use it, but the app will
work with a local MongoDB instance when present.

This file intentionally tolerates both string and ObjectId forms for
stored user IDs and order.user_id fields.
"""

from __future__ import annotations

import os
import warnings
from typing import Any, Dict

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

load_dotenv()

warnings.filterwarnings(
    "ignore",
    message=r"You appear to be connected to a CosmosDB cluster.*",
    category=UserWarning,
)

# Make Cosmos DB optional. Prefer local MongoDB when available.
_raw_cosmos_uri = os.getenv("COSMOS_DB_URI", "").strip()
_cosmos_placeholder_tokens = ("USERNAME", "PASSWORD", "YOUR-COSMOS-ACCOUNT", "your-cosmos-account")
COSMOS_DB_URI = (
    _raw_cosmos_uri
    if _raw_cosmos_uri and not any(token in _raw_cosmos_uri for token in _cosmos_placeholder_tokens)
    else None
)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

DB_NAME = (
    os.getenv("COSMOS_DB_NAME")
    or os.getenv("COSMOS_DATABASE_NAME")
    or os.getenv("MONGO_DB_NAME")
    or "smart_retail"
)


def _create_cosmos_client() -> MongoClient:
    if not COSMOS_DB_URI:
        raise RuntimeError("COSMOS_DB_URI is not set; Cosmos client cannot be created.")
    try:
        return MongoClient(
            COSMOS_DB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            retryWrites=False,
        )
    except PyMongoError as exc:
        raise RuntimeError(f"Failed to initialize Cosmos MongoClient: {exc}") from exc


def _create_local_client() -> MongoClient:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        socketTimeoutMS=3000,
    )
    # perform a ping to ensure the server is reachable
    client.admin.command("ping")
    return client


# --- Initialize Clients ---
cosmos_client = None
cosmos_db = None
if COSMOS_DB_URI:
    try:
        cosmos_client = _create_cosmos_client()
        cosmos_db = cosmos_client[DB_NAME]
    except Exception:
        cosmos_client = None
        cosmos_db = None

# Try to connect to local MongoDB first. If available, prefer it.
try:
    local_client = _create_local_client()
    local_db = local_client[DB_NAME]
    LOCAL_DB_AVAILABLE = True
except (PyMongoError, ServerSelectionTimeoutError):
    local_client = None
    local_db = None
    LOCAL_DB_AVAILABLE = False

# Allow forcing CosmosDB even when local MongoDB is available.
USE_COSMOS_ONLY = os.getenv("USE_COSMOS_ONLY", "false").strip().lower() in ("1", "true", "yes")

# --- Primary database selection ---
# Use local MongoDB when available; otherwise use Cosmos DB if configured.
if USE_COSMOS_ONLY:
    if cosmos_db is None:
        raise RuntimeError("USE_COSMOS_ONLY is set but COSMOS_DB_URI is not configured or failed to connect.")
    PRIMARY_DB = cosmos_db
elif LOCAL_DB_AVAILABLE:
    PRIMARY_DB = local_db
elif cosmos_db is not None:
    PRIMARY_DB = cosmos_db
else:
    raise RuntimeError(
        "No database available: could not connect to local MongoDB and COSMOS_DB_URI is not set or failed."
    )


# --- App collections ---
users_collection: Collection[Dict[str, Any]] = PRIMARY_DB["users"]
products_collection: Collection[Dict[str, Any]] = PRIMARY_DB["products"]
orders_collection: Collection[Dict[str, Any]] = PRIMARY_DB["orders"]
carts_collection: Collection[Dict[str, Any]] = PRIMARY_DB["carts"]
retail_analytics_collection: Collection[Dict[str, Any]] = PRIMARY_DB["retail_analytics"]

# --- Operational collections (prefer local DB if available) ---
op_db = local_db if local_db is not None else PRIMARY_DB
chat_logs_collection: Collection[Dict[str, Any]] = op_db["chat_logs"]
documents_collection: Collection[Dict[str, Any]] = op_db["documents"]
sales_collection: Collection[Dict[str, Any]] = op_db["sales"]

# Startup diagnostic for database selection
_db_host = getattr(PRIMARY_DB.client, 'address', None)
_db_address = f"{_db_host[0]}:{_db_host[1]}" if _db_host else 'unknown'
print(f"[db.py] PRIMARY_DB={PRIMARY_DB.name}, host={_db_address}, LOCAL_DB_AVAILABLE={LOCAL_DB_AVAILABLE}, USE_COSMOS_ONLY={USE_COSMOS_ONLY}")


def test_connection() -> bool:
    """Return True when the configured database connections respond to a ping."""
    try:
        if cosmos_client is not None:
            cosmos_client.admin.command("ping")
        if local_client is not None:
            local_client.admin.command("ping")
        return True
    except PyMongoError as exc:
        raise RuntimeError(f"Database connection test failed: {exc}") from exc


if __name__ == "__main__":
    try:
        print("Testing Database connections...")
        print("Connection OK:", test_connection())
    except Exception as exc:  # pragma: no cover
        print("Connection test failed:", exc)
