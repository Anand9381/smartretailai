"""Incremental replication of local `orders` to Cosmos DB (Mongo API).

Behavior:
- Uses a local `replication_state` collection to remember last replicated `created_at`.
- By default runs once in dry-run mode (no writes). Use --no-dry-run and --run-once to perform one replication.
- Will NOT create the `orders` collection in Cosmos by default; use --force-create to allow that (not recommended on low RU accounts).
- Handles RU-limit OperationFailure by backing off and aborting gracefully.

Usage examples:
  # Dry-run once (default)
  python scripts/replicate_orders_to_cosmos.py --run-once

  # Real replication once
  python scripts/replicate_orders_to_cosmos.py --run-once --no-dry-run

  # Continuous replication every 30s
  python scripts/replicate_orders_to_cosmos.py --interval 30

"""

import os
import sys
import time
import argparse
from pymongo import ReplaceOne
from pymongo.errors import PyMongoError, OperationFailure

# Ensure project root is importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from db import local_db, cosmos_db
except Exception as exc:
    print("Failed to import db.py:", exc)
    sys.exit(2)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--batch-size", type=int, default=100)
    p.add_argument("--pause", type=float, default=1.0, help="Seconds to sleep between batches")
    p.add_argument("--interval", type=float, default=None, help="If set, run continuously with this many seconds between runs")
    p.add_argument("--run-once", action="store_true", default=False, help="Run a single replication pass and exit")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True, help="Do not perform writes")
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Perform writes to Cosmos")
    p.add_argument("--force-create", action="store_true", help="Allow creating the orders collection in Cosmos (use carefully)")
    return p.parse_args()


def get_last_replicated_at(rep_state_coll):
    doc = rep_state_coll.find_one({"collection": "orders"})
    if not doc:
        return 0
    return doc.get("last_replicated_at", 0)


def set_last_replicated_at(rep_state_coll, ts):
    rep_state_coll.update_one({"collection": "orders"}, {"$set": {"last_replicated_at": ts}}, upsert=True)


def replicate_once(batch_size, pause, dry_run, force_create):
    rep_state_coll = local_db["replication_state"]
    orders_local = local_db["orders"]
    orders_cosmos = cosmos_db["orders"]

    last_ts = get_last_replicated_at(rep_state_coll)
    print(f"Last replicated created_at={last_ts}")

    # Check if cosmos has orders collection
    cosmos_has_orders = "orders" in cosmos_db.list_collection_names()
    print("Cosmos has orders collection:", cosmos_has_orders)
    if not cosmos_has_orders and not force_create:
        print("Orders collection does not exist in Cosmos. Skipping replication. Use --force-create to attempt creation (may fail due to RU limits).")
        return True

    cursor = orders_local.find({"created_at": {"$gt": last_ts}}).sort("created_at", 1).batch_size(batch_size)
    to_upsert = []
    processed = 0
    max_ts = last_ts
    try:
        for doc in cursor:
            # Ensure documents are serializable for Cosmos (ObjectId is fine)
            to_upsert.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))
            if doc.get("created_at", 0) > max_ts:
                max_ts = doc.get("created_at", 0)
            if len(to_upsert) >= batch_size:
                if dry_run:
                    processed += len(to_upsert)
                    print(f"[dry-run] Would upsert batch of {len(to_upsert)} documents (processed {processed})")
                else:
                    try:
                        res = orders_cosmos.bulk_write(to_upsert, ordered=False)
                        processed += len(to_upsert)
                        print(f"Upserted batch: {processed}")
                    except OperationFailure as exc:
                        print("OperationFailure during bulk_write:", exc)
                        if "total throughput" in str(exc) or "Substatus: 1028" in str(exc):
                            print("RU limit hit. Aborting replication pass.")
                            return False
                        raise
                to_upsert = []
                time.sleep(pause)
        # final flush
        if to_upsert:
            if dry_run:
                processed += len(to_upsert)
                print(f"[dry-run] Would upsert final batch of {len(to_upsert)} documents (processed {processed})")
            else:
                try:
                    res = orders_cosmos.bulk_write(to_upsert, ordered=False)
                    processed += len(to_upsert)
                    print(f"Upserted final batch: {processed}")
                except OperationFailure as exc:
                    print("OperationFailure during final bulk_write:", exc)
                    if "total throughput" in str(exc) or "Substatus: 1028" in str(exc):
                        print("RU limit hit. Aborting replication pass.")
                        return False
                    raise
        # update last_replicated_at
        if not dry_run and processed > 0:
            set_last_replicated_at(rep_state_coll, max_ts)
            print(f"Updated last_replicated_at to {max_ts}")
        elif dry_run:
            print("Dry-run complete. No state updated.")
        else:
            print("No new documents to replicate.")
    except PyMongoError as exc:
        print("PyMongoError during replication:", exc)
        return False
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    return True


def main():
    args = parse_args()
    if args.run_once:
        ok = replicate_once(args.batch_size, args.pause, args.dry_run, args.force_create)
        if not ok:
            print("Replication pass failed or aborted.")
            sys.exit(1)
        print("Replication pass finished.")
        return

    # Continuous loop
    print("Starting continuous replication loop. Press Ctrl+C to stop.")
    try:
        while True:
            ok = replicate_once(args.batch_size, args.pause, args.dry_run, args.force_create)
            if not ok:
                print("Replication pass aborted due to error or RU limit. Backing off for 30s.")
                time.sleep(30)
            interval = args.interval if args.interval is not None else 10
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopping replication")


if __name__ == "__main__":
    main()
