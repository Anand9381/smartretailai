from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import csv
from functools import wraps
from bson import ObjectId
from datetime import datetime
from db import orders_collection, users_collection, carts_collection, products_collection, sales_collection
from routes.chat_api import chat_api
from services.ml_service import detect_anomalies_lazy, predict_sales_lazy
import requests
try:
    import msal
except Exception:
    msal = None

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static",
    static_url_path="/static",
)
app.register_blueprint(chat_api)

# simple session secret
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-change-me')

# MongoDB collections come from db.py so the whole app uses the same configured database.
_users = users_collection
_products = products_collection
_sales = sales_collection


def _seed_db_if_empty():
    # seed products
    if _products.count_documents({}) == 0:
        sample = [
            {'slug': 'headphones-pro', 'name': 'Wireless Headphones Pro', 'category': 'Electronics', 'price': 199.0, 'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700', 'desc': 'Noise cancelation + 30hr battery', 'stock': 34, 'badge': 'Trending'},
            {'slug': 'watch-ultra', 'name': 'Smart Watch Ultra', 'category': 'Electronics', 'price': 349.0, 'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=700', 'desc': 'Health tracking + premium design', 'stock': 12, 'badge': 'New'},
            {'slug': 'designer-shades', 'name': 'Designer Sunglasses', 'category': 'Fashion', 'price': 129.0, 'image': 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=700', 'desc': 'UV400 polarized lenses', 'stock': 58, 'badge': 'Hot'},
            {'slug': 'coffee-maker', 'name': 'Premium Coffee Maker', 'category': 'Home & Kitchen', 'price': 89.0, 'image': 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=700', 'desc': 'Programmable brew + thermal mode', 'stock': 6, 'badge': 'Sale'},
        ]
        _products.insert_many(sample)

    # seed sales from CSV if empty
    if _sales.count_documents({}) == 0:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
        csv_path = os.path.normpath(csv_path)
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            docs = []
            for _, r in df.iterrows():
                docs.append({'date': str(pd.to_datetime(r['date']).date()), 'sales': float(r['sales'])})
            if docs:
                _sales.insert_many(docs)
        except Exception:
            # ignore if CSV missing
            pass


def _ensure_bootstrap_user(email_env, password_env, role, name):
    email = os.environ.get(email_env)
    password = os.environ.get(password_env)
    if not email or not password:
        return

    user = users_collection.find_one({'email': email})
    password_hash = generate_password_hash(password)
    if user:
        update = {'role': role}
        if not user.get('password') or email in {os.environ.get('ADMIN_EMAIL'), os.environ.get('DEMO_USER_EMAIL')}:
            update['password'] = password_hash
        if not user.get('name'):
            update['name'] = name
        users_collection.update_one({'_id': user['_id']}, {'$set': update})
        return

    users_collection.insert_one({
        'name': name,
        'email': email,
        'password': password_hash,
        'role': role,
    })


def _ensure_bootstrap_users():
    _ensure_bootstrap_user('ADMIN_EMAIL', 'ADMIN_PASSWORD', 'admin', 'Admin')
    _ensure_bootstrap_user('DEMO_USER_EMAIL', 'DEMO_USER_PASSWORD', 'user', 'Demo User')


# seed DB at startup (safe: only inserts when empty)
#_seed_db_if_empty()
if os.environ.get("ENABLE_BOOTSTRAP_USERS", "false").strip().lower() in ("1", "true", "yes"):
    try:
        # Bootstrap users if requested. Guard against DB/network errors so
        # the app can still start when the database is unreachable at import time.
        _ensure_bootstrap_users()
    except Exception as exc:
        # Log and continue; runtime DB operations will surface errors where they are handled.
        print(f"[application.py] Warning: bootstrap users skipped due to error: {exc}")


@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/home")
def public_landing():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('user_id'):
            if request.path.startswith('/api/'):
                return jsonify({'ok': False, 'error': 'authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return inner


def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if session.get('role') != 'admin':
            if request.path.startswith('/api/') or request.path.startswith('/admin/powerbi/'):
                return jsonify({'ok': False, 'error': 'Admin authentication required'}), 403
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return inner


def _to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    return value


def _current_user_id():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return _to_object_id(user_id)


def _serialize_order(order: dict) -> dict:
    created_at = order.get('created_at')
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    delivery_date = order.get('delivery_date')
    if isinstance(delivery_date, datetime):
        delivery_date = delivery_date.isoformat()
    items = order.get('items') or []
    count = int(order.get('count') or sum(int(item.get('qty', 1)) for item in items))
    total = order.get('total')
    if total is None:
        total = sum((float(item.get('price') or 0) * int(item.get('qty') or 1)) for item in items)
    try:
        total = float(total)
    except Exception:
        total = 0.0
    return {
        'id': str(order.get('_id') or ''),
        'order_code': order.get('order_code'),
        'created_at': created_at or datetime.utcnow().isoformat(),
        'status': str(order.get('status', 'Ordered')).title(),
        'total': total,
        'count': count,
        'items': items,
        'payment_method': order.get('payment_method') or 'UPI',
        'delivery_date': delivery_date,
        'delivery_label': order.get('delivery_label') or 'Delivery Date',
    }


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("user_dashboard.html")


@app.route("/cart")
@login_required
def cart_page():
    return render_template("cart.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route("/products")
def products():
    # fetch products from DB
    prods = list(_products.find({}, {'_id': 0}))
    return render_template("products.html", products=prods)


@app.route("/products/<product_id>")
def product_detail(product_id):
    prod = _products.find_one({'slug': product_id}, {'_id': 0})
    if not prod:
        # fallback: render with id
        return render_template("product_detail.html", product_id=product_id)
    return render_template("product_detail.html", product=prod)


@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html")


@app.route("/chat")
@login_required
def customer_chat():
    return render_template("chat.html")


### API endpoints: authentication and ML


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    name = data.get('name') or data.get('full_name')
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    requested_role = (data.get('role') or 'user').strip().lower()
    role = 'admin' if requested_role == 'admin' else 'user'
    admin_secret = data.get('admin_secret')
    if not email or not password:
        return jsonify({'ok': False, 'error': 'email and password required'}), 400

    try:
        if users_collection.find_one({'email': email}):
            return jsonify({'ok': False, 'error': 'user exists'}), 400
    except Exception as exc:
        return jsonify({'ok': False, 'error': 'database unavailable', 'detail': str(exc)}), 503

    if role == 'admin' and os.environ.get('ADMIN_SECRET') != admin_secret:
        return jsonify({'ok': False, 'error': 'Invalid admin secret. Please use Customer Account or enter the correct admin secret.'}), 403

    user = {
        'name': name or '',
        'email': email,
        'password': generate_password_hash(password),
        'role': role,
    }
    try:
        users_collection.insert_one(user)
    except Exception as exc:
        return jsonify({'ok': False, 'error': 'database unavailable', 'detail': str(exc)}), 503
    session.pop('user_id', None)
    session.pop('role', None)
    redirect = '/login'
    return jsonify({'ok': True, 'role': role, 'redirect': redirect})


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    requested_role = (data.get('role') or 'user').strip().lower()
    requested_role = 'admin' if requested_role == 'admin' else 'user'
    if not email or not password:
        return jsonify({'ok': False, 'error': 'email and password required'}), 400

    try:
        user = users_collection.find_one({'email': email})
    except Exception as exc:
        return jsonify({'ok': False, 'error': 'database unavailable', 'detail': str(exc)}), 503
    password_hash = user.get('password') if user else None
    valid_password = bool(password_hash) and check_password_hash(password_hash, password)
    if not user or not valid_password:
        return jsonify({'ok': False, 'error': 'invalid credentials'}), 401

    actual_role = user.get('role', 'user')
    if requested_role != actual_role:
        return jsonify({'ok': False, 'error': f'This account is registered as {actual_role}. Please use {actual_role.title()} Login.'}), 403

    session['user_id'] = str(user.get('_id'))
    session['role'] = actual_role
    redirect = '/admin/dashboard' if session['role'] == 'admin' else '/dashboard'
    return jsonify({'ok': True, 'role': session['role'], 'redirect': redirect})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return jsonify({'ok': True})


@app.route('/api/predict')
def api_predict():
    # Accept ?day=42 or ?date=2024-01-15
    day = request.args.get('day')
    date = request.args.get('date')
    try:
        if day is not None:
            pred = predict_sales_lazy(int(day))
        elif date is not None:
            pred = predict_sales_lazy(date)
        else:
            return jsonify({'ok': False, 'error': 'provide day or date'}), 400
        return jsonify({'ok': True, 'prediction': pred})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/anomalies')
def api_anomalies():
    try:
        df = detect_anomalies_lazy()
        # convert to simple list
        if df.empty:
            return jsonify({'ok': True, 'anomalies': []})
        out = []
        for _, row in df.iterrows():
            out.append({'date': str(row['date']), 'sales': float(row['sales']), 'type': row['anomaly_type']})
        return jsonify({'ok': True, 'anomalies': out})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/products')
def api_products():
    prods = list(_products.find({}, {'_id': 0}))
    return jsonify({'ok': True, 'products': prods})


@app.route('/api/cart')
def api_cart():
    if not session.get('user_id'):
        return jsonify({'ok': False, 'error': 'authentication required'}), 401
    user_id = _current_user_id()
    cart_doc = carts_collection.find_one({'user_id': user_id})
    return jsonify({'ok': True, 'cart': {'items': cart_doc.get('items', []) if cart_doc else []}})


@app.route('/api/add-to-cart', methods=['POST'])
def api_add_to_cart():
    if not session.get('user_id'):
        return jsonify({'ok': False, 'error': 'authentication required'}), 401
    data = request.get_json() or {}
    slug = data.get('slug')
    qty = int(data.get('qty', 1) or 1)
    if not slug or qty <= 0:
        return jsonify({'ok': False, 'error': 'slug and qty required'}), 400

    product = _products.find_one({'slug': slug}, {'_id': 0})
    if not product:
        return jsonify({'ok': False, 'error': 'product not found'}), 404

    user_id = _current_user_id()
    cart_doc = carts_collection.find_one({'user_id': user_id}) or {'user_id': user_id, 'items': []}
    items = cart_doc.get('items', [])
    found = False
    for item in items:
        if item.get('slug') == slug:
            item['qty'] = int(item.get('qty', 0)) + qty
            found = True
            break
    if not found:
        items.append({
            'slug': slug,
            'qty': qty,
            'name': product.get('name'),
            'price': float(product.get('price') or 0),
            'category': product.get('category'),
            'image': product.get('image'),
        })

    carts_collection.update_one(
        {'user_id': user_id},
        {'$set': {'items': items, 'updated_at': datetime.utcnow()}},
        upsert=True,
    )
    return jsonify({'ok': True, 'cart': {'items': items}})


@app.route('/api/remove-from-cart', methods=['DELETE'])
def api_remove_from_cart():
    if not session.get('user_id'):
        return jsonify({'ok': False, 'error': 'authentication required'}), 401
    data = request.get_json() or {}
    slug = data.get('slug')
    if not slug:
        return jsonify({'ok': False, 'error': 'slug required'}), 400

    user_id = _current_user_id()
    cart_doc = carts_collection.find_one({'user_id': user_id})
    if not cart_doc:
        return jsonify({'ok': True, 'cart': {'items': []}})

    items = [item for item in cart_doc.get('items', []) if item.get('slug') != slug]
    carts_collection.update_one(
        {'user_id': user_id},
        {'$set': {'items': items, 'updated_at': datetime.utcnow()}},
        upsert=True,
    )
    return jsonify({'ok': True, 'cart': {'items': items}})


@app.route('/api/orders', methods=['GET', 'POST'])
def api_orders():
    if request.method == 'GET':
        if not session.get('user_id'):
            return jsonify({'ok': False, 'error': 'authentication required'}), 401
        user_id = _current_user_id()
        raw_orders = list(orders_collection.find({'user_id': user_id}).sort('created_at', -1))
        orders = [_serialize_order(order) for order in raw_orders]
        return jsonify({'ok': True, 'orders': orders})

    data = request.get_json() or {}
    items = data.get('items') or []
    if not isinstance(items, list) or not items:
        return jsonify({'ok': False, 'error': 'order items are required'}), 400

    user_id = _current_user_id() if session.get('user_id') else None
    total = 0.0
    count = 0
    for item in items:
        qty = int(item.get('qty', 1) or 1)
        price = float(item.get('price', 0) or 0)
        total += qty * price
        count += qty

    new_order = {
        'items': items,
        'user_id': user_id,
        'created_at': datetime.utcnow(),
        'status': 'Ordered',
        'order_code': f"SR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        'total': total,
        'count': count,
        'payment_method': 'UPI',
        'delivery_date': datetime.utcnow(),
    }
    result = orders_collection.insert_one(new_order)
    return jsonify({'ok': True, 'message': 'Order placed successfully', 'order_id': str(result.inserted_id)})


@app.route('/api/place-order', methods=['POST'])
def api_place_order():
    if not session.get('user_id'):
        return jsonify({'ok': False, 'error': 'authentication required'}), 401
    data = request.get_json(silent=True) or {}
    items = data.get('items') if isinstance(data, dict) else None
    user_id = _current_user_id()
    if not items:
        cart_doc = carts_collection.find_one({'user_id': user_id})
        items = cart_doc.get('items', []) if cart_doc else []

    if not isinstance(items, list) or not items:
        return jsonify({'ok': False, 'error': 'cart is empty'}), 400

    total = 0.0
    count = 0
    for item in items:
        qty = int(item.get('qty', 1) or 1)
        price = float(item.get('price', 0) or 0)
        total += qty * price
        count += qty

    order = {
        'items': items,
        'user_id': user_id,
        'created_at': datetime.utcnow(),
        'status': 'Ordered',
        'order_code': f"SR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        'total': total,
        'count': count,
        'payment_method': 'UPI',
        'delivery_date': datetime.utcnow(),
    }
    result = orders_collection.insert_one(order)
    carts_collection.update_one(
        {'user_id': user_id},
        {'$set': {'items': [], 'updated_at': datetime.utcnow()}},
        upsert=True,
    )
    return jsonify({'ok': True, 'message': 'Order placed successfully', 'order_id': str(result.inserted_id)})


@app.route('/api/sales_series')
@admin_required
def api_sales_series():
    # return dates and sales from sales collection
    docs = list(_sales.find({}, {'_id': 0}).sort('date', 1))
    dates = [d['date'] for d in docs]
    sales = [d['sales'] for d in docs]
    return jsonify({'ok': True, 'dates': dates, 'sales': sales})


@app.route('/api/category_share')
@admin_required
def api_category_share():
    pipeline = [
        {'$group': {'_id': '$category', 'count': {'$sum': 1}}}
    ]
    rows = list(_products.aggregate(pipeline))
    labels = [r['_id'] for r in rows]
    vals = [r['count'] for r in rows]
    return jsonify({'ok': True, 'labels': labels, 'values': vals})


### Inventory CRUD


@app.route('/api/inventory', methods=['GET'])
@admin_required
def api_inventory_list():
    prods = list(_products.find({}, {'_id': 0}))
    return jsonify({'ok': True, 'products': prods})


@app.route('/api/inventory', methods=['POST'])
@admin_required
def api_inventory_create():
    data = request.get_json() or {}
    required = ['slug', 'name', 'price']
    if not all(k in data for k in required):
        return jsonify({'ok': False, 'error': 'slug,name,price required'}), 400
    data.setdefault('stock', 0)
    _products.insert_one(data)
    return jsonify({'ok': True})


@app.route('/api/inventory/<slug>', methods=['PUT', 'PATCH'])
@admin_required
def api_inventory_update(slug):
    data = request.get_json() or {}
    update = {}
    for k in ('name', 'price', 'stock', 'desc', 'category', 'badge', 'image'):
        if k in data:
            update[k] = data[k]
    if not update:
        return jsonify({'ok': False, 'error': 'no fields to update'}), 400
    _products.update_one({'slug': slug}, {'$set': update})
    return jsonify({'ok': True})


@app.route('/api/inventory/<slug>', methods=['DELETE'])
@admin_required
def api_inventory_delete(slug):
    _products.delete_one({'slug': slug})
    return jsonify({'ok': True})


def _build_powerbi_snapshot_data():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    rows = []
    try:
        with open(os.path.join(data_dir, "retail_master_dataset.csv"), "r", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except Exception:
        rows = []

    labels = []
    monthly_sales = []
    predicted_sales = []
    scatter_points = []
    stock_risk = {"Low Risk": 0, "Medium Risk": 0, "High Risk": 0}

    for row in rows:
        name = row.get("name", "")
        if not name:
            continue
        monthly = float(row.get("monthlySales") or 0)
        growth = float(row.get("salesGrowth") or 0)
        predicted = max(0, round(monthly * (1 + growth / 100), 1))
        current_stock = float(row.get("currentStock") or 0)
        stock_status = str(row.get("stockStatus") or "")
        views = float(row.get("monthlyViews") or 0)
        cart_adds = float(row.get("cartAdds") or 0)

        if stock_status in ("Critical Stock", "Out Of Stock"):
            risk = "High Risk"
        elif stock_status == "Low Stock":
            risk = "Medium Risk"
        else:
            risk = "Low Risk"
        stock_risk[risk] += current_stock

        labels.append(name)
        monthly_sales.append(monthly)
        predicted_sales.append(predicted)
        scatter_points.append({
            "x": monthly,
            "y": predicted,
            "r": max(5, min(20, round((views + cart_adds) / 500))),
            "name": name,
            "category": row.get("category", "General"),
        })

    return {
        "labels": labels,
        "monthlySales": monthly_sales,
        "predictedFutureSales": predicted_sales,
        "stockRiskLabels": list(stock_risk.keys()),
        "stockRiskValues": list(stock_risk.values()),
        "scatterPoints": scatter_points,
    }


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    total_sales = 0.0
    try:
        total_orders = orders_collection.count_documents({})
        total_products = products_collection.count_documents({})
        low_stock_count = products_collection.count_documents({"stock": {"$lte": 10}})
        for order in orders_collection.find({}, {"total": 1, "amount": 1, "grand_total": 1}):
            total_sales += float(order.get("total") or order.get("amount") or order.get("grand_total") or 0)
    except Exception:
        total_orders = 0
        total_products = 0
        low_stock_count = 0

    data_dir = os.path.join(os.path.dirname(__file__), "data")

    def _load_json_file(filename, default):
        try:
            with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return default

    monitoring_data = _load_json_file("product_monitoring_data.json", [])
    analytics_data = _load_json_file("analytics_prediction_data.json", [])
    retail_master_rows = []
    try:
        with open(os.path.join(data_dir, "retail_master_dataset.csv"), "r", encoding="utf-8") as fh:
            retail_master_rows = list(csv.DictReader(fh))
    except Exception:
        retail_master_rows = []

    def _growth_value(item):
        try:
            return float(str(item.get("salesGrowth", "0")).replace("%", "").replace("+", ""))
        except Exception:
            return 0.0

    monitoring_by_name = {item.get("name"): item for item in monitoring_data}
    top_trending = sorted(monitoring_data, key=lambda item: item.get("trendingScore", 0), reverse=True)[:4]
    stock_alerts = [
        item for item in monitoring_data
        if item.get("stockStatus") in ("Low Stock", "Critical Stock", "Out Of Stock")
    ]
    active_offers = [
        item for item in monitoring_data
        if str(item.get("activeOffer", "")).lower() not in ("", "none", "no offer", "no active offer")
    ][:5]
    high_demand = sorted(analytics_data, key=_growth_value, reverse=True)[:4]
    restock_priority = [
        item for item in analytics_data
        if any(token in str(item.get("stockPrediction", "")).lower() for token in ("out of stock", "critical", "recommended", "2 weeks"))
    ]
    restock_priority.sort(key=lambda item: (monitoring_by_name.get(item.get("name"), {}).get("stock", 999), -_growth_value(item)))

    dashboard_insights = {
        "top_trending": top_trending,
        "stock_alerts": stock_alerts,
        "active_offers": active_offers,
        "high_demand": high_demand,
        "restock_priority": restock_priority[:4],
        "monitoring_by_name": monitoring_by_name,
    }

    stock_status_counts = {}
    for item in monitoring_data:
        status = item.get("stockStatus") or "Unknown"
        stock_status_counts[status] = stock_status_counts.get(status, 0) + 1

    powerbi_snapshot_data = _build_powerbi_snapshot_data()
    dashboard_chart_data = {
        "salesLabels": powerbi_snapshot_data["labels"],
        "monthlySales": powerbi_snapshot_data["monthlySales"],
        "predictedFutureSales": powerbi_snapshot_data["predictedFutureSales"],
        "stockStatusLabels": list(stock_status_counts.keys()),
        "stockStatusValues": list(stock_status_counts.values()),
    }

    powerbi_public_embed_url = os.getenv("POWERBI_PUBLIC_EMBED_URL") or (
        "https://app.powerbi.com/reportEmbed"
        "?reportId=b25d55f1-4089-44ca-9fd7-71f3d36f4e62"
        "&autoAuth=true"
        "&ctid=78303038-f9b4-463e-9080-60b2496e5793"
        "&filterPaneEnabled=false"
        "&navContentPaneEnabled=false"
    )
    powerbi_report_link = os.getenv("POWERBI_REPORT_LINK") or (
        "https://app.powerbi.com/groups/me/reports/b25d55f1-4089-44ca-9fd7-71f3d36f4e62/3e3960cb6a55302f057c?experience=power-bi&clientSideAuth=0"
    )
    return render_template(
        "admin_dashboard.html",
        total_sales=round(total_sales, 2),
        total_orders=total_orders,
        total_products=total_products,
        low_stock_count=low_stock_count,
        powerbi_public_embed_url=powerbi_public_embed_url,
        powerbi_report_link=powerbi_report_link,
        dashboard_insights=dashboard_insights,
        dashboard_chart_data=dashboard_chart_data,
        powerbi_snapshot_data=powerbi_snapshot_data,
    )


@app.route("/admin/analytics")
@admin_required
def admin_analytics():
    powerbi_report_link = os.getenv("POWERBI_REPORT_LINK") or (
        "https://app.powerbi.com/groups/me/reports/b25d55f1-4089-44ca-9fd7-71f3d36f4e62/3e3960cb6a55302f057c?experience=power-bi"
    )
    return render_template(
        "admin_analytics.html",
        powerbi_report_link=powerbi_report_link,
        powerbi_snapshot_data=_build_powerbi_snapshot_data(),
        powerbi_tenant_id=os.getenv("POWERBI_TENANT_ID", "78303038-f9b4-463e-9080-60b2496e5793"),
    )


@app.route('/admin/powerbi/embed-info')
@admin_required
def admin_powerbi_embed_info():
    """Return Power BI embed information (embedUrl + embed token).

    Requires the following environment variables to be set for secure embedding:
      - POWERBI_CLIENT_ID
      - POWERBI_CLIENT_SECRET
      - POWERBI_TENANT_ID
      - POWERBI_GROUP_ID
      - POWERBI_REPORT_ID

    If these are not configured the endpoint returns an error explaining what's missing.
    """
    client_id = os.getenv('POWERBI_CLIENT_ID')
    client_secret = os.getenv('POWERBI_CLIENT_SECRET')
    tenant_id = os.getenv('POWERBI_TENANT_ID')
    group_id = os.getenv('POWERBI_GROUP_ID')
    report_id = os.getenv('POWERBI_REPORT_ID')

    if not all([client_id, client_secret, tenant_id, group_id, report_id]):
        public_embed_url = os.getenv('POWERBI_PUBLIC_EMBED_URL')
        report_link = os.getenv('POWERBI_REPORT_LINK')
        if public_embed_url:
            return jsonify({
                'ok': True,
                'mode': 'public',
                'embedUrl': public_embed_url,
                'reportLink': report_link,
                'warning': 'Secure Power BI embedding is not configured. Using public embed URL fallback.',
            })
        return jsonify({'ok': False, 'error': 'Power BI embedding not configured. Set POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID, POWERBI_GROUP_ID, POWERBI_REPORT_ID or POWERBI_PUBLIC_EMBED_URL'}), 400

    if msal is None:
        return jsonify({'ok': False, 'error': 'msal library not installed. pip install msal'}), 500

    # Acquire AAD token using client credentials
    authority = f'https://login.microsoftonline.com/{tenant_id}'
    app_msal = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_resp = app_msal.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
    if 'access_token' not in token_resp:
        return jsonify({'ok': False, 'error': 'Failed to acquire AAD token for Power BI', 'details': token_resp}), 500
    access_token = token_resp['access_token']

    # Get report metadata to obtain the embedUrl
    rep_url = f'https://api.powerbi.com/v1.0/myorg/groups/{group_id}/reports/{report_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get(rep_url, headers=headers)
    if r.status_code != 200:
        return jsonify({'ok': False, 'error': 'Failed to fetch report metadata', 'status_code': r.status_code, 'body': r.text}), 500
    rep_meta = r.json()
    embed_url = rep_meta.get('embedUrl')

    # Generate embed token for the report
    gen_url = f'https://api.powerbi.com/v1.0/myorg/groups/{group_id}/reports/{report_id}/GenerateToken'
    body = { 'accessLevel': 'View' }
    r2 = requests.post(gen_url, headers={**headers, 'Content-Type': 'application/json'}, json=body)
    if r2.status_code not in (200, 201):
        return jsonify({'ok': False, 'error': 'Failed to generate embed token', 'status_code': r2.status_code, 'body': r2.text}), 500
    token_json = r2.json()
    embed_token = token_json.get('token') or token_json.get('embedToken') or token_json

    return jsonify({'ok': True, 'embedUrl': embed_url, 'embedToken': embed_token, 'reportId': report_id, 'groupId': group_id})


@app.route("/admin/inventory")
@admin_required
def admin_inventory():
    return render_template("admin_inventory.html")


def _normalize_order(order: dict) -> dict:
    user_label = "Unknown"
    user_id = order.get("user_id")
    if user_id:
        try:
            if isinstance(user_id, ObjectId):
                user_doc = users_collection.find_one({"_id": user_id})
            elif isinstance(user_id, str) and ObjectId.is_valid(user_id):
                user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
            else:
                user_doc = users_collection.find_one({"email": user_id})
            if user_doc:
                user_label = user_doc.get("name") or user_doc.get("email") or str(user_id)
            else:
                user_label = str(user_id)
        except Exception:
            user_label = str(user_id)

    items = order.get("items") or []
    product_label = "N/A"
    quantity = 0
    if isinstance(items, list) and items:
        names = []
        for item in items:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("product") or item.get("title") or "Item")
                quantity += int(item.get("quantity") or item.get("qty") or item.get("count") or 0)
            else:
                names.append(str(item))
                quantity += 1
        product_label = ", ".join(names[:2]) + ("..." if len(names) > 2 else "")
    else:
        product_label = order.get("product") or "N/A"
        quantity = int(order.get("quantity") or order.get("qty") or order.get("count") or 0)

    created_at = order.get("created_at") or order.get("date") or order.get("order_date")
    if isinstance(created_at, (int, float)):
        try:
            order_date = datetime.utcfromtimestamp(created_at).strftime("%Y-%m-%d")
        except Exception:
            order_date = str(created_at)
    else:
        order_date = str(created_at or "")

    status = str(order.get("status", "Pending")).title()
    total = order.get("total")
    try:
        total = f"{float(total):.2f}"
    except Exception:
        total = str(total or "0.00")

    return {
        "id": str(order.get("_id") or ""),
        "user": user_label,
        "product": product_label,
        "quantity": quantity,
        "status": status,
        "date": order_date,
        "total": total,
    }


@app.route("/admin/orders")
@admin_required
def admin_orders():
    raw_orders = list(orders_collection.find({}).sort("created_at", -1).limit(200))
    orders = [_normalize_order(o) for o in raw_orders]
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/chat")
@admin_required
def admin_chat():
    return render_template("admin_chat.html")

@app.route("/admin/monitoring")
@admin_required
def admin_monitoring():
    return render_template("admin_monitoring.html")

@app.route("/admin/forecast")
@admin_required
def admin_forecast():
    return render_template("admin_forecast.html")

@app.route("/api/admin/forecast-data")
@admin_required
def api_forecast_data():
    path = os.path.join(os.path.dirname(__file__), 'data', 'forecastData.json')
    with open(path, 'r') as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
