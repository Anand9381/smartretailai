import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

def test_endpoints():
    """Test all admin endpoints"""
    with app.test_client() as client:
        # Set admin session
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['user_email'] = 'admin@example.com'
            sess['user_id'] = 'test-admin'
        
        endpoints = [
            ('/api/sales_series', 'GET', 'Sales series'),
            ('/api/category_share', 'GET', 'Category share'),
            ('/api/inventory', 'GET', 'Inventory'),
            ('/api/products', 'GET', 'Products'),
            ('/api/predict', 'GET', 'ML Predict'),
            ('/api/anomalies', 'GET', 'Anomalies'),
            ('/api/admin/forecast-data', 'GET', 'Admin forecast data'),
            ('/api/orders', 'GET', 'Orders'),
        ]
        
        for endpoint, method, desc in endpoints:
            try:
                if method == 'GET':
                    resp = client.get(endpoint)
                else:
                    resp = client.post(endpoint)
                
                status = resp.status_code
                is_ok = status in [200, 201]
                symbol = '✓' if is_ok else '✗'
                print(f'{symbol} {desc:25} {endpoint:30} → {status}')
                
                if not is_ok and status < 400:
                    print(f'  → {resp.get_json()}')
            except Exception as e:
                print(f'✗ {desc:25} {endpoint:30} → ERROR: {str(e)[:50]}')

if __name__ == '__main__':
    test_endpoints()
