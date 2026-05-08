"""Seed all data into MongoDB: products, users, analytics, and documents."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db import (
    products_collection,
    users_collection,
    test_connection,
    retail_analytics_collection,
    documents_collection,
)


def seed_products() -> int:
    """Load products from products_seed.json into MongoDB."""
    products_file = Path(PROJECT_ROOT) / "data" / "products_seed.json"
    
    if not products_file.exists():
        print(f"❌ Products file not found: {products_file}")
        return 0
    
    with open(products_file, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    if not isinstance(products, list):
        products = [products]
    
    # Clear existing products (optional - comment out if you want to keep old ones)
    products_collection.delete_many({})
    
    inserted = products_collection.insert_many(products)
    print(f"✅ Seeded {len(inserted.inserted_ids)} products into database")
    return len(inserted.inserted_ids)


def seed_users() -> int:
    """Create admin and demo users."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    demo_email = os.getenv("DEMO_USER_EMAIL", "user@example.com")
    demo_password = os.getenv("DEMO_USER_PASSWORD", "User123!")
    
    users_to_create = [
        {
            "email": admin_email,
            "name": "Admin User",
            "password": generate_password_hash(admin_password),
            "role": "admin",
        },
        {
            "email": demo_email,
            "name": "Demo User",
            "password": generate_password_hash(demo_password),
            "role": "user",
        },
    ]
    
    created = 0
    for user in users_to_create:
        existing = users_collection.find_one({"email": user["email"]})
        if existing:
            users_collection.update_one({"email": user["email"]}, {"$set": user})
            print(f"✅ Updated user: {user['email']}")
        else:
            users_collection.insert_one(user)
            print(f"✅ Created user: {user['email']}")
            created += 1
    
    return created


def seed_analytics_data() -> int:
    """Load sample analytics data."""
    analytics_file = Path(PROJECT_ROOT) / "data" / "analytics_prediction_data.json"
    
    if not analytics_file.exists():
        print(f"⚠️  Analytics file not found: {analytics_file} (skipping)")
        return 0
    
    try:
        with open(analytics_file, "r", encoding="utf-8") as f:
            analytics_data = json.load(f)
        
        if not isinstance(analytics_data, list):
            analytics_data = [analytics_data]
        
        # Clear existing (optional)
        retail_analytics_collection.delete_many({})
        
        inserted = retail_analytics_collection.insert_many(analytics_data)
        print(f"✅ Seeded {len(inserted.inserted_ids)} analytics records")
        return len(inserted.inserted_ids)
    except Exception as e:
        print(f"⚠️  Failed to load analytics data: {e}")
        return 0


def seed_sample_documents() -> int:
    """Load sample business documents."""
    docs_dir = Path(PROJECT_ROOT) / "documents"
    
    if not docs_dir.exists():
        print(f"⚠️  Documents directory not found: {docs_dir}")
        return 0
    
    # Define key documents to load
    doc_files = {
        "return_policy.md": "Return Policy",
        "shipping_policy.md": "Shipping Policy",
        "warranty_rules.md": "Warranty Rules",
        "promotions_discounts.md": "Promotions & Discounts",
        "inventory_rules.md": "Inventory Rules",
        "faq.md": "FAQ",
    }
    
    created = 0
    for filename, title in doc_files.items():
        doc_path = docs_dir / filename
        if not doc_path.exists():
            print(f"⚠️  Document not found: {filename}")
            continue
        
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        doc = {
            "title": title,
            "filename": filename,
            "content": content,
            "type": "policy" if "policy" in filename.lower() else "document",
        }
        
        existing = documents_collection.find_one({"filename": filename})
        if existing:
            documents_collection.update_one({"filename": filename}, {"$set": doc})
            print(f"✅ Updated document: {title}")
        else:
            documents_collection.insert_one(doc)
            print(f"✅ Loaded document: {title}")
            created += 1
    
    return created


def main() -> None:
    """Run all seeding operations."""
    print("\n" + "="*60)
    print("🚀 SmartRetailAI - MongoDB Data Seeding")
    print("="*60 + "\n")
    
    # Test connection
    try:
        print("Testing MongoDB connection...")
        test_connection()
        print("✅ Connection successful!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Run all seeds
    products_count = seed_products()
    users_count = seed_users()
    analytics_count = seed_analytics_data()
    documents_count = seed_sample_documents()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Seeding Summary:")
    print("="*60)
    print(f"  Products:     {products_count} loaded")
    print(f"  Users:        {users_count} created/updated")
    print(f"  Analytics:    {analytics_count} records loaded")
    print(f"  Documents:    {documents_count} loaded")
    
    # Final counts
    total_products = products_collection.count_documents({})
    total_users = users_collection.count_documents({})
    total_analytics = retail_analytics_collection.count_documents({})
    total_docs = documents_collection.count_documents({})
    
    print(f"\n📈 Total in Database:")
    print(f"  Products:     {total_products}")
    print(f"  Users:        {total_users}")
    print(f"  Analytics:    {total_analytics}")
    print(f"  Documents:    {total_docs}")
    print("\n✨ Seeding complete!\n")


if __name__ == "__main__":
    main()
