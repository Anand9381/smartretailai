"""Initialize Azure Cosmos DB with starter users and sample data.

This script is idempotent and can be run multiple times.
It is intended to make Cosmos documents visible immediately in the Azure Portal
while keeping the app itself Cosmos-backed through pymongo.
"""

from __future__ import annotations

import os

from werkzeug.security import generate_password_hash

from db import (
    products_collection,
    test_connection,
    users_collection,
)


DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123!")
DEFAULT_USER_EMAIL = os.environ.get("DEMO_USER_EMAIL", "user@example.com")
DEFAULT_USER_PASSWORD = os.environ.get("DEMO_USER_PASSWORD", "User123!")


def upsert_user(email: str, name: str, password: str, role: str) -> None:
    existing = users_collection.find_one({"email": email})
    payload = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": role,
    }
    if existing:
        users_collection.update_one({"email": email}, {"$set": payload})
        print(f"Updated {role} user: {email}")
    else:
        users_collection.insert_one(payload)
        print(f"Created {role} user: {email}")


def main() -> None:
    print("Testing Cosmos DB connection...")
    print("Connection OK:", test_connection())

    upsert_user(DEFAULT_ADMIN_EMAIL, "Admin", DEFAULT_ADMIN_PASSWORD, "admin")
    upsert_user(DEFAULT_USER_EMAIL, "Demo User", DEFAULT_USER_PASSWORD, "user")

    print(f"Users collection count: {users_collection.count_documents({})}")
    print(f"Products collection count: {products_collection.count_documents({})}")
    print("Cosmos initialization complete.")


if __name__ == "__main__":
    main()
