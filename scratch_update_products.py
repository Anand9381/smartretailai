import json
import os
from db import products_collection

def update_products():
    seed_path = os.path.join(os.path.dirname(__file__), 'data', 'products_seed.json')
    with open(seed_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    for p in products:
        products_collection.update_one({'slug': p['slug']}, {'$set': {'desc': p['desc']}})
    
    print("Products updated successfully!")

if __name__ == "__main__":
    update_products()
