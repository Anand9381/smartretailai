"""Copy collections from local MongoDB to Azure Cosmos DB (Mongo API).

This script is intentionally conservative:
- By default it only syncs collections that already exist in Cosmos (no collection creation).
- Default mode is a dry-run: it reports counts and batch estimates without performing writes.
- Use --no-dry-run to perform upserts in batches with a pause between batches to throttle RU.

Usage examples:
  # Dry-run (default)
  python scripts/copy_collections_to_cosmos.py

  # Real run for collections users and products (careful with RU)
  python scripts/copy_collections_to_cosmos.py --collections users,products --no-dry-run --batch-size 100 --pause 1

"""

import os
import sys
import time
import argparse
from pymongo import ReplaceOne
from pymongo.errors import PyMongoError, OperationFailure

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from db import cosmos_db, local_db
except Exception as exc:
    print("Failed to import db.py:", exc)
    sys.exit(2)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collections", help="Comma-separated list of collections to sync. Default: intersection of local and cosmos", default=None)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--pause", type=float, default=1.0, help="Seconds to sleep between batches to throttle RU usage")
    # Dry-run default True; use --no-dry-run to execute writes
    parser.add_argument("--dry-run", action="store_true", default=True, help=argparse.SUPPRESS)
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Perform actual upserts instead of dry-run")
    parser.add_argument("--force-create", action="store_true", help="Allow creating collections on Cosmos if missing (use with caution)")
    return parser.parse_args()


def copy_collection(coll_name, batch_size, pause, dry_run):
    local_coll = local_db[coll_name]
    cosmos_coll = cosmos_db[coll_name]
    total = local_coll.count_documents({})
    print(f"\nCollection: {coll_name} local count={total} cosmos_exists={coll_name in cosmos_db.list_collection_names()}")
    if dry_run:
        print(f"[dry-run] Would upsert {total} documents in batches of {batch_size}.")
        return True

    cursor = local_coll.find({}, no_cursor_timeout=True).batch_size(batch_size)
    ops = []
    processed = 0
    try:
        for doc in cursor:
            ops.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))
            if len(ops) >= batch_size:
                result = cosmos_coll.bulk_write(ops, ordered=False)
                processed += len(ops)
                print(f"  Upserted batch: {processed}/{total}")
                ops = []
                time.sleep(pause)
        if ops:
            result = cosmos_coll.bulk_write(ops, ordered=False)
            processed += len(ops)
            print(f"  Upserted final batch: {processed}/{total}")
    except OperationFailure as exc:
        print("OperationFailure while copying:", exc)
        print("Aborting copy for collection:", coll_name)
        return False
    except PyMongoError as exc:
        print("PyMongoError while copying:", exc)
        return False
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    return True


def main():
    args = parse_args()
    local_cols = set(local_db.list_collection_names())
    cosmos_cols = set(cosmos_db.list_collection_names())
    if args.collections:
        to_sync = [c.strip() for c in args.collections.split(",") if c.strip()]
    else:
        # Default: sync only collections that already exist in Cosmos (safe)
        to_sync = sorted(list(local_cols & cosmos_cols))

    print("Local collections:", sorted(list(local_cols)))
    print("Cosmos collections:", sorted(list(cosmos_cols)))
    print("Collections selected for sync:", to_sync)

    if not to_sync:
        print("No collections selected for safe sync. Use --collections or --force-create to override.")
        return

    for coll in to_sync:
        ok = copy_collection(coll, args.batch_size, args.pause, args.dry_run)
        if not ok:
            print("Stopped due to error copying collection:", coll)
            break


if __name__ == "__main__":
    main()
