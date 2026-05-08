import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import orders_collection, products_collection, users_collection
print('orders count:', orders_collection.count_documents({}))
print('products count:', products_collection.count_documents({}))
print('users count:', users_collection.count_documents({}))
for o in orders_collection.find().limit(3):
    print(o)
