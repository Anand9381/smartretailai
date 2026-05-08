#!/usr/bin/env python
"""
Complete Admin Functionality Testing Script
Tests all pages, endpoints, and features
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

def run_complete_tests():
    """Run comprehensive admin tests"""
    print("\n" + "="*100)
    print("SMARTRETAILAI - COMPLETE ADMIN FUNCTIONALITY TEST")
    print("="*100)
    
    with app.test_client() as client:
        # Set admin session
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['user_email'] = 'admin@example.com'
            sess['user_id'] = 'test-admin'
        
        # ============ SECTION 1: ADMIN PAGES ============
        print("\n[SECTION 1] ADMIN PAGES & NAVIGATION")
        print("-" * 100)
        
        pages = [
            ('/admin/dashboard', 'Dashboard - KPIs, charts, alerts'),
            ('/admin/inventory', 'Inventory - Manage products'),
            ('/admin/forecast', 'ML Forecast - Demand prediction charts'),
            ('/admin/analytics', 'Analytics - Power BI embed'),
            ('/admin/orders', 'Orders - View all customer orders'),
            ('/admin/chat', 'Chat - Admin assistant'),
            ('/admin/monitoring', 'Monitoring - Product anomaly detection'),
        ]
        
        page_results = []
        for url, desc in pages:
            resp = client.get(url)
            status = resp.status_code
            ok = status == 200
            symbol = '✓' if ok else '✗'
            print(f"  {symbol} {desc:50} [{url}] → {status}")
            
            if ok:
                html = resp.get_data(as_text=True)
                # Check for JS files
                has_chart_js = 'chart' in html.lower()
                has_scripts = '<script' in html
                print(f"     └─ Has Chart.js: {has_chart_js}, Scripts: {has_scripts}")
            
            page_results.append((url, ok))
        
        # ============ SECTION 2: CORE DATA ENDPOINTS ============
        print("\n[SECTION 2] CORE DATA ENDPOINTS")
        print("-" * 100)
        
        endpoints = [
            ('/api/sales_series', 'Sales time series'),
            ('/api/category_share', 'Product category distribution'),
            ('/api/inventory', 'Product inventory'),
            ('/api/products', 'All products catalog'),
            ('/api/anomalies', 'Anomaly detection results'),
            ('/api/admin/forecast-data', 'ML forecast predictions'),
            ('/api/orders', 'All customer orders'),
        ]
        
        api_results = []
        for url, desc in endpoints:
            resp = client.get(url)
            status = resp.status_code
            ok = status == 200
            symbol = '✓' if ok else '✗'
            
            data = resp.get_json() if ok else {}
            data_summary = ''
            
            if isinstance(data, list):
                data_summary = f" ({len(data)} items)"
            elif isinstance(data, dict):
                if 'ok' in data:
                    data_summary = f" (ok={data.get('ok')})"
                elif 'products' in data:
                    data_summary = f" ({len(data.get('products', []))} products)"
                elif 'anomalies' in data:
                    data_summary = f" ({len(data.get('anomalies', []))} anomalies)"
                elif 'orders' in data:
                    data_summary = f" ({len(data.get('orders', []))} orders)"
            
            print(f"  {symbol} {desc:40} [{url}] → {status}{data_summary}")
            api_results.append((url, ok))
        
        # ============ SECTION 3: ADMIN-SPECIFIC ENDPOINTS ============
        print("\n[SECTION 3] ADMIN OPERATIONS")
        print("-" * 100)
        
        # Test chat
        chat_payload = {
            'message': 'What is the total sales revenue?',
            'history': []
        }
        resp = client.post('/chat/admin', 
                          json=chat_payload,
                          headers={'Content-Type': 'application/json'})
        status = resp.status_code
        ok = status == 200
        symbol = '✓' if ok else '✗'
        print(f"  {symbol} {'Admin Chat API':40} [/chat/admin] → {status}")
        if ok:
            data = resp.get_json()
            resp_len = len(data.get('response', ''))
            print(f"     └─ Response length: {resp_len} chars")
        
        # ============ SECTION 4: FORECAST FUNCTIONALITY ============
        print("\n[SECTION 4] FORECAST PAGE FUNCTIONALITY")
        print("-" * 100)
        
        # Get forecast page
        resp = client.get('/admin/forecast')
        if resp.status_code == 200:
            html = resp.get_data(as_text=True)
            
            checks = [
                ('Has ml_forecast.js', '/static/js/ml_forecast.js' in html or 'ml_forecast.js' in html),
                ('Has Chart.js', 'chart.js' in html.lower()),
                ('Has demandLineChart canvas', 'demandLineChart' in html),
                ('Has correlationScatterPlot canvas', 'correlationScatterPlot' in html),
                ('Has productGrowthCards div', 'productGrowthCards' in html),
                ('Has aiInsights div', 'aiInsights' in html),
                ('Has forecast data fetch', '/api/admin/forecast-data' in html),
            ]
            
            for check_name, check_result in checks:
                symbol = '✓' if check_result else '✗'
                print(f"  {symbol} {check_name:40}")
        
        # ============ SECTION 5: INVENTORY FUNCTIONALITY ============
        print("\n[SECTION 5] INVENTORY PAGE FUNCTIONALITY")
        print("-" * 100)
        
        resp = client.get('/admin/inventory')
        if resp.status_code == 200:
            html = resp.get_data(as_text=True)
            
            checks = [
                ('Has inventory.js', 'inventory.js' in html),
                ('Has product form', 'inventoryCreateForm' in html),
                ('Has product table', 'orders-table' in html),
                ('Has inventory API fetch', '/api/inventory' in html),
            ]
            
            for check_name, check_result in checks:
                symbol = '✓' if check_result else '✗'
                print(f"  {symbol} {check_name:40}")
        
        # ============ SECTION 6: DASHBOARD FUNCTIONALITY ============
        print("\n[SECTION 6] DASHBOARD PAGE FUNCTIONALITY")
        print("-" * 100)
        
        resp = client.get('/admin/dashboard')
        if resp.status_code == 200:
            html = resp.get_data(as_text=True)
            
            checks = [
                ('Has dashboard.js', 'dashboard.js' in html),
                ('Has sales chart', 'salesChart' in html),
                ('Has category chart', 'categoryChart' in html),
                ('Has KPI section', 'kpi-section' in html),
                ('Has Power BI iframe', 'powerbi.com' in html),
            ]
            
            for check_name, check_result in checks:
                symbol = '✓' if check_result else '✗'
                print(f"  {symbol} {check_name:40}")
        
        # ============ FINAL SUMMARY ============
        print("\n[SUMMARY]")
        print("-" * 100)
        
        pages_ok = sum(1 for _, ok in page_results if ok)
        apis_ok = sum(1 for _, ok in api_results if ok)
        
        print(f"  Pages Passing:       {pages_ok}/{len(page_results)}")
        print(f"  APIs Passing:        {apis_ok}/{len(api_results)}")
        print(f"  Total:               {pages_ok + apis_ok}/{len(page_results) + len(api_results)}")
        
        if pages_ok == len(page_results) and apis_ok == len(api_results):
            print("\n  ✓✓✓ ALL ADMIN FEATURES FULLY FUNCTIONAL ✓✓✓")
            print("\n  Admin Dashboard:     http://127.0.0.1:5000/admin/dashboard")
            print("  Admin Email:         admin@example.com")
            print("  Admin Password:      Admin123!")
        else:
            print("\n  ⚠ Some components need attention")
        
        print("\n" + "="*100 + "\n")

if __name__ == '__main__':
    run_complete_tests()
