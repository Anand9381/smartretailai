#!/usr/bin/env python
"""Test forecast and orders endpoints"""
from app import app

with app.app_context():
    with app.test_client() as client:
        # Test forecast API
        resp = client.get('/api/admin/forecast-data')
        print(f'Forecast API status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.get_json()
            print(f'Forecast data type: {type(data).__name__}')
            if isinstance(data, list):
                print(f'Items: {len(data)}')
                if len(data) > 0:
                    print(f'Sample keys: {list(data[0].keys())}')
            elif isinstance(data, dict):
                print(f'Keys: {list(data.keys())}')
        else:
            print(f'Error response: {resp.get_json()}')
        
        # Check orders endpoint
        with client.session_transaction() as sess:
            sess['user_id'] = '123'
            sess['role'] = 'admin'
        
        resp = client.get('/api/orders')
        print(f'\nOrders API status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.get_json()
            print(f'Orders response: {data}')
