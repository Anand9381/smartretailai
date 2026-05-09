import os

from werkzeug.security import generate_password_hash
from db import test_connection, users_collection

email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')

try:
    print('MongoDB connection:', test_connection())
except Exception as exc:
    print('Connection test failed:', exc)
    raise SystemExit(1)

u = users_collection.find_one({'email': email})
if u:
    print('User already exists:', u.get('email'), 'role=', u.get('role'))
else:
    users_collection.insert_one({'name': 'Admin', 'email': email, 'password': generate_password_hash(password), 'role': 'admin'})
    print('Created admin user:', email)
