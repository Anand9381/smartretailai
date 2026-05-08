import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

def test_admin_pages():
    """Test all admin pages for rendering and broken references"""
    with app.test_client() as client:
        # Set admin session
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['user_email'] = 'admin@example.com'
            sess['user_id'] = 'test-admin'
        
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
        
        print("Testing Admin Pages\n")
        print("-" * 80)
        
        for endpoint, desc in pages:
            try:
                resp = client.get(endpoint)
                status = resp.status_code
                is_ok = status == 200
                symbol = '✓' if is_ok else '✗'
                print(f'{symbol} {desc:25} {endpoint:30} → {status}')
                
                if is_ok:
                    html = resp.get_data(as_text=True)
                    # Check for common issues
                    if 'Traceback' in html or 'Error' in html or '<title>Error' in html:
                        print(f'  ⚠ Page has error content!')
                    if 'url_for' in html:
                        print(f'  ⚠ Page has unrendered Jinja2 expressions!')
                elif status in [302, 301]:
                    print(f'  → Redirect to: {resp.headers.get("Location", "unknown")}')
                    
            except Exception as e:
                print(f'✗ {desc:25} {endpoint:30} → ERROR: {str(e)[:50]}')

if __name__ == '__main__':
    test_admin_pages()
