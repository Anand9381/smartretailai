#!/usr/bin/env python
"""
Comprehensive Admin Feature Verification Script
Tests all admin endpoints, pages, and data loading
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

def test_admin_features():
    """Test all admin components systematically"""
    print("="*90)
    print("ADMIN FEATURE VERIFICATION TEST")
    print("="*90)
    
    with app.test_client() as client:
        # Set admin session
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['user_email'] = 'admin@example.com'
            sess['user_id'] = 'test-admin'
        
        # 1. Test Pages
        print("\n[1] ADMIN PAGES")
        print("-" * 90)
        pages = [
            ('/admin/dashboard', 'Dashboard'),
            ('/admin/inventory', 'Inventory'),
            ('/admin/forecast', 'Forecast'),
            ('/admin/ml-forecast', 'ML Forecast Alias'),
            ('/admin/analytics', 'Analytics/PowerBI'),
            ('/admin/orders', 'Orders'),
            ('/admin/chat', 'Chat'),
            ('/admin/monitoring', 'Monitoring'),
        ]
        
        page_results = []
        for endpoint, desc in pages:
            resp = client.get(endpoint)
            status = resp.status_code
            is_ok = status == 200
            symbol = '✓' if is_ok else '✗'
            print(f'  {symbol} {desc:25} {endpoint:30} → {status}')
            page_results.append((desc, is_ok))
        
        # 2. Test APIs
        print("\n[2] ADMIN APIS")
        print("-" * 90)
        apis = [
            ('/api/sales_series', 'GET', 'Sales Series'),
            ('/api/category_share', 'GET', 'Category Share'),
            ('/api/inventory', 'GET', 'Inventory'),
            ('/api/products', 'GET', 'Products'),
            ('/api/anomalies', 'GET', 'Anomalies'),
            ('/api/admin/forecast-data', 'GET', 'Forecast Data'),
            ('/api/orders', 'GET', 'Orders'),
        ]
        
        api_results = []
        for endpoint, method, desc in apis:
            try:
                if method == 'GET':
                    resp = client.get(endpoint)
                
                status = resp.status_code
                is_ok = status == 200
                symbol = '✓' if is_ok else '✗'
                print(f'  {symbol} {desc:25} {endpoint:30} → {status}')
                
                if is_ok:
                    data = resp.get_json()
                    if isinstance(data, list):
                        print(f'     └─ Data: {len(data)} items')
                    elif isinstance(data, dict) and 'ok' in data:
                        print(f'     └─ Data: ok={data.get("ok")}')
                
                api_results.append((desc, is_ok))
            except Exception as e:
                print(f'  ✗ {desc:25} {endpoint:30} → ERROR')
                api_results.append((desc, False))
        
        # 3. Test Chat Endpoints
        print("\n[3] CHAT ENDPOINTS")
        print("-" * 90)
        
        # Test admin chat
        chat_data = {
            'message': 'What is total sales?',
            'history': []
        }
        try:
            resp = client.post('/chat/admin', 
                             json=chat_data,
                             headers={'Content-Type': 'application/json'})
            status = resp.status_code
            is_ok = status == 200
            symbol = '✓' if is_ok else '✗'
            print(f'  {symbol} Admin Chat                 /chat/admin              → {status}')
            if is_ok:
                data = resp.get_json()
                print(f'     └─ Response: {len(data.get("response", ""))} chars')
        except Exception as e:
            print(f'  ✗ Admin Chat                 /chat/admin              → ERROR')
        
        # 4. Summary
        print("\n[4] SUMMARY")
        print("-" * 90)
        
        pages_pass = sum(1 for _, ok in page_results if ok)
        apis_pass = sum(1 for _, ok in api_results if ok)
        
        print(f"  Pages:     {pages_pass}/{len(page_results)} passed")
        print(f"  APIs:      {apis_pass}/{len(api_results)} passed")
        print(f"  Total:     {pages_pass + apis_pass}/{len(page_results) + len(api_results)} passed")
        
        if pages_pass == len(page_results) and apis_pass == len(api_results):
            print("\n  ✓ ALL TESTS PASSED - Admin side is fully functional!")
        else:
            print("\n  ⚠ Some tests failed - Review output above")
        
        print("\n" + "="*90)

if __name__ == '__main__':
    test_admin_features()
