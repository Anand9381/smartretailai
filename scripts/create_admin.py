"""Create an admin user in local MongoDB for development testing.

Usage:
  python scripts/create_admin.py --email admin@example.com --password Admin123!

This will insert a user into smart_retail.users with role 'admin'.
"""
import argparse
import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

parser = argparse.ArgumentParser()
parser.add_argument('--email', required=True)
parser.add_argument('--password', required=True)
args = parser.parse_args()

mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client.get_database('smart_retail')
users = db.get_collection('users')

if users.find_one({'email': args.email}):
    print('User already exists:', args.email)
else:
    users.insert_one({'name': 'Admin', 'email': args.email, 'password': generate_password_hash(args.password), 'role': 'admin'})
    print('Created admin user:', args.email)
