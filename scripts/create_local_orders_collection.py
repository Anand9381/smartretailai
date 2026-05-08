"""Create a local `orders` collection by inserting a single sample order.

This is a conservative local bootstrap used when Cosmos cannot accept a new
collection due to RU limits.
"""

import os
import sys
import time
from pymongo.errors import PyMongoError, OperationFailure

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from db import orders_collection, local_db
except Exception as exc:
    print("Failed to import db.py:", exc)
    sys.exit(2)


def main():
    doc = {
        "user_id": "local-bootstrap",
        "items": [],
        "total": 0.0,
        "created_at": int(time.time()),
        "note": "local bootstrap orders collection"
    }
    try:
        print("Attempting insert into local orders_collection...")
        res = orders_collection.insert_one(doc)
        print("Insert OK, _id:", res.inserted_id)
        print("Collections in LOCAL DB:", local_db.list_collection_names())
    except OperationFailure as exc:
        print("OperationFailure during insert:\n", exc)
        sys.exit(3)
    except PyMongoError as exc:
        print("PyMongoError during insert:\n", exc)
        sys.exit(4)


if __name__ == "__main__":
    main()
