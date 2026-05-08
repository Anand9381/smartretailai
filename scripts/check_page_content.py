import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

def check_page_content():
    """Check page content for issues"""
    with app.test_client() as client:
        # Set admin session
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['user_email'] = 'admin@example.com'
            sess['user_id'] = 'test-admin'
        
        endpoint = '/admin/forecast'
        resp = client.get(endpoint)
        html = resp.get_data(as_text=True)
        
        # Print first 2000 chars
        print("Page content (first 2000 chars):")
        print(html[:2000])
        print("\n...\n")
        print("Page content (last 2000 chars):")
        print(html[-2000:])

if __name__ == '__main__':
    check_page_content()
