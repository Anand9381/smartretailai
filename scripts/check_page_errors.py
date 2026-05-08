import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

def check_page_errors():
    """Check what errors are in the problem pages"""
    with app.test_client() as client:
        # Set admin session
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['user_email'] = 'admin@example.com'
            sess['user_id'] = 'test-admin'
        
        problem_pages = [
            ('/admin/forecast', 'Forecast'),
            ('/admin/analytics', 'Analytics'),
        ]
        
        for endpoint, desc in problem_pages:
            print(f"\n{'='*80}")
            print(f"Page: {desc} ({endpoint})")
            print('='*80)
            resp = client.get(endpoint)
            html = resp.get_data(as_text=True)
            
            # Look for error messages
            if 'Traceback' in html:
                start = html.find('Traceback')
                end = html.find('</pre>', start)
                if end == -1:
                    end = start + 1000
                print("Error found:")
                print(html[start:end][:800])

if __name__ == '__main__':
    check_page_errors()
