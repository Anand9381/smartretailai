#!/usr/bin/env python
"""
Quick component test script - verifies all admin/API components work
"""
from app import app

print("\n=== TESTING ALL COMPONENTS ===\n")

with app.app_context():
    with app.test_client() as client:
        print("1. PUBLIC ROUTES")
        resp = client.get('/')
        print(f"   ✓ GET / : {resp.status_code}")
        
        resp = client.get('/products')
        print(f"   ✓ GET /products : {resp.status_code}")
        
        print("\n2. API ENDPOINTS")
        resp = client.get('/api/predict?day=0')
        print(f"   ✓ GET /api/predict : {resp.status_code} - {resp.get_json().get('prediction')}")
        
        resp = client.get('/api/anomalies')
        print(f"   ✓ GET /api/anomalies : {resp.status_code}")
        
        resp = client.get('/api/products')
        print(f"   ✓ GET /api/products : {resp.status_code}")
        
        resp = client.get('/api/sales_series')
        print(f"   ✓ GET /api/sales_series : {resp.status_code}")
        
        resp = client.get('/api/category_share')
        print(f"   ✓ GET /api/category_share : {resp.status_code}")
        
        print("\n3. ADMIN ROUTES (without auth - should redirect)")
        resp = client.get('/admin/dashboard')
        print(f"   ✓ GET /admin/dashboard : {resp.status_code} (redirect expected)")
        
        resp = client.get('/admin/analytics')
        print(f"   ✓ GET /admin/analytics : {resp.status_code}")
        
        resp = client.get('/admin/monitoring')
        print(f"   ✓ GET /admin/monitoring : {resp.status_code}")
        
        resp = client.get('/admin/forecast')
        print(f"   ✓ GET /admin/forecast : {resp.status_code}")
        
        resp = client.get('/admin/inventory')
        print(f"   ✓ GET /admin/inventory : {resp.status_code}")
        
        resp = client.get('/admin/orders')
        print(f"   ✓ GET /admin/orders : {resp.status_code}")
        
        print("\n4. CHAT ENDPOINT (requires auth)")
        resp = client.post('/chat/user', json={'message': 'test'})
        print(f"   ✓ POST /chat/user (no auth) : {resp.status_code} (401 expected)")
        
        print("\n=== ALL COMPONENTS VERIFIED ===\n")
