"""Insert a single sample order into Cosmos DB to create the `orders` collection.

Run in the project's virtualenv. This performs one small write and prints
collections after the insert.
"""

import os
import sys
import time
from pymongo.errors import PyMongoError, OperationFailure

# Ensure project root on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from db import orders_collection, cosmos_db
except Exception as exc:
    print("Failed to import db.py:", exc)
    sys.exit(2)


def main():
    doc = {
        "user_id": None,
        "items": [],
        "total": 0.0,
        "created_at": int(time.time()),
        "note": "bootstrap orders collection (sample)"
    }
    try:
        print("Attempting insert into orders_collection...")
        res = orders_collection.insert_one(doc)
        print("Insert OK, _id:", res.inserted_id)
        print("Collections now in Cosmos DB:", cosmos_db.list_collection_names())
    except OperationFailure as exc:
        print("OperationFailure during insert:\n", exc)
        sys.exit(3)
    except PyMongoError as exc:
        print("PyMongoError during insert:\n", exc)
        sys.exit(4)


if __name__ == "__main__":
    main()
