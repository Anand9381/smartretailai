"""Test script: ping Cosmos, list collections, and attempt a small insert into products.

Run this with your virtualenv active. It uses the project's `db.py` to ensure
we use the same configuration the app uses.
"""

import time
import sys
import os
from pymongo.errors import PyMongoError, OperationFailure

# Ensure project root is on sys.path so `from db import ...` works when running
# this script directly.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # db.py exports cosmos_client, cosmos_db, products_collection
    from db import cosmos_client, cosmos_db, products_collection
except Exception as exc:
    print("Failed to import db.py:", exc)
    sys.exit(2)


def main():
    try:
        print("Pinging Cosmos (admin)...")
        cosmos_client.admin.command("ping")
        print("Ping OK")
    except PyMongoError as exc:
        print("Ping failed:", exc)
        return

    try:
        cols = cosmos_db.list_collection_names()
        print("Collections in Cosmos DB:", cols)
    except PyMongoError as exc:
        print("Failed to list collections:", exc)

    doc = {
        "slug": f"push-test-{int(time.time())}",
        "name": "Push Test Product",
        "price": 0.01,
        "stock": 1,
    }
    try:
        print("Attempting insert into products_collection...")
        res = products_collection.insert_one(doc)
        print("Insert OK, _id:", res.inserted_id)
    except OperationFailure as exc:
        print("OperationFailure during insert:\n", exc)
    except PyMongoError as exc:
        print("PyMongoError during insert:\n", exc)
    except Exception as exc:
        print("Unexpected error during insert:\n", exc)


if __name__ == "__main__":
    main()
