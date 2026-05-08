from flask import Blueprint, request, jsonify, session
from functools import wraps
from agents.customer_agent import CustomerAgent
from agents.admin_assistant_agent import AdminAssistantAgent

chat_api = Blueprint("chat_api", __name__, url_prefix="/chat")

_customer_agent = None
_admin_agent = None

def get_customer_agent():
    global _customer_agent
    if _customer_agent is None:
        _customer_agent = CustomerAgent()
    return _customer_agent

def get_admin_agent():
    global _admin_agent
    if _admin_agent is None:
        _admin_agent = AdminAssistantAgent()
    return _admin_agent

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "user":
            return jsonify({"ok": False, "error": "User authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            return jsonify({"ok": False, "error": "Admin authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@chat_api.route("/user", methods=["POST"])
@user_required
def chat_user():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"ok": False, "error": "message required"}), 400

    agent = get_customer_agent()
    try:
        response = agent.chat(message, session.get("user_id"))
        return jsonify({"ok": True, "response": response})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Chat error: {str(e)}"}), 500

@chat_api.route("/admin", methods=["POST"])
@admin_required
def chat_admin():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"ok": False, "error": "message required"}), 400

    agent = get_admin_agent()
    try:
        response = agent.chat(message, session.get("user_id"))
        return jsonify({"ok": True, "response": response})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Chat error: {str(e)}"}), 500
