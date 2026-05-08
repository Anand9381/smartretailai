import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

with app.test_client() as client:
    # set admin session
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_email'] = 'admin@example.com'

    resp = client.get('/api/admin/forecast-data')
    print('forecast-data status:', resp.status_code)
    try:
        data = resp.get_json()
        print('forecast-data length:', len(data) if data else 0)
        print('first item:', json.dumps(data[0], indent=2))
    except Exception as e:
        print('forecast-data error:', e)

    resp2 = client.get('/admin/orders')
    print('/admin/orders status:', resp2.status_code)
    # print snippet of HTML to confirm orders table present
    html = resp2.get_data(as_text=True)
    found = 'No orders found' in html
    print('admin/orders reports no orders found in template?:', found)
    # show first table row if present
    if not found:
        start = html.find('<tbody>')
        end = html.find('</tbody>', start)
        print(html[start:end][:1000])
