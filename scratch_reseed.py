import json
import os
from db import products_collection

def reseed():
    seed_path = os.path.join(os.path.dirname(__file__), 'data', 'products_seed.json')
    with open(seed_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    products_collection.delete_many({})
    products_collection.insert_many(products)
    print("Products collection dropped and re-seeded successfully!")

if __name__ == "__main__":
    reseed()
