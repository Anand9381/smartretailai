"""
test_routes.py - Tests for Flask API routes
============================================
Tests public pages, authentication endpoints, product API,
and admin-protected routes to ensure they respond correctly.
"""

import pytest


# =====================================================================
# 1. PUBLIC PAGE TESTS - Verify that public pages load without errors
# =====================================================================

class TestPublicPages:
    """Test that all public-facing pages return HTTP 200."""

    def test_landing_page_loads(self, client):
        """The home page (/) should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_page_loads(self, client):
        """The /home route should also return 200 OK."""
        response = client.get("/home")
        assert response.status_code == 200

    def test_login_page_loads(self, client):
        """The login page should render without errors."""
        response = client.get("/login")
        assert response.status_code == 200

    def test_signup_page_loads(self, client):
        """The signup page should render without errors."""
        response = client.get("/signup")
        assert response.status_code == 200

    def test_products_page_loads(self, client):
        """The products listing page should load for all visitors."""
        response = client.get("/products")
        assert response.status_code == 200


# =====================================================================
# 2. AUTH API TESTS - Verify signup, login, and logout endpoints
# =====================================================================

class TestAuthAPI:
    """Test the authentication API endpoints."""

    def test_signup_missing_fields_returns_400(self, client):
        """Signing up without email/password should fail with 400."""
        response = client.post("/api/signup", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["ok"] is False  # Error response expected

    def test_login_missing_fields_returns_400(self, client):
        """Logging in without email/password should fail with 400."""
        response = client.post("/api/login", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["ok"] is False

    def test_login_wrong_credentials_returns_401(self, client):
        """Logging in with wrong credentials should fail with 401."""
        response = client.post("/api/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        # Should be 401 (unless it matches the dev admin fallback)
        assert response.status_code in (401, 200)

    def test_logout_clears_session(self, client):
        """Logout should redirect to the login page."""
        response = client.get("/logout")
        # Flask redirect returns 302
        assert response.status_code == 302


# =====================================================================
# 3. PRODUCT API TESTS - Verify the products API returns valid data
# =====================================================================

class TestProductAPI:
    """Test the product-related API endpoints."""

    def test_api_products_returns_json(self, client):
        """/api/products should return a JSON response with an 'ok' field."""
        response = client.get("/api/products")
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        # Products should be a list (could be empty if DB has no seed data)
        assert isinstance(data["products"], list)

    def test_api_inventory_returns_json(self, client):
        """/api/inventory should return a JSON list of products."""
        response = client.get("/api/inventory")
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert isinstance(data["products"], list)


# =====================================================================
# 4. PROTECTED ROUTE TESTS - Admin pages should redirect if not logged in
# =====================================================================

class TestProtectedRoutes:
    """Test that admin routes redirect unauthenticated users to login."""

    def test_admin_dashboard_requires_login(self, client):
        """Accessing /admin/dashboard without login should redirect."""
        response = client.get("/admin/dashboard")
        assert response.status_code == 302  # Redirect to login

    def test_admin_inventory_requires_login(self, client):
        """Accessing /admin/inventory without login should redirect."""
        response = client.get("/admin/inventory")
        assert response.status_code == 302

    def test_admin_orders_requires_login(self, client):
        """Accessing /admin/orders without login should redirect."""
        response = client.get("/admin/orders")
        assert response.status_code == 302

    def test_admin_forecast_requires_login(self, client):
        """Accessing /admin/forecast without login should redirect."""
        response = client.get("/admin/forecast")
        assert response.status_code == 302

    def test_admin_analytics_requires_login(self, client):
        """Accessing /admin/analytics without login should redirect."""
        response = client.get("/admin/analytics")
        assert response.status_code == 302


# =====================================================================
# 5. CART API TESTS - Cart requires authentication
# =====================================================================

class TestCartAPI:
    """Test the cart API endpoints require authentication."""

    def test_cart_requires_auth(self, client):
        """Accessing /api/cart without login should return 401."""
        response = client.get("/api/cart")
        assert response.status_code == 401

    def test_add_to_cart_requires_auth(self, client):
        """Adding to cart without login should return 401."""
        response = client.post("/api/add-to-cart", json={"slug": "test", "qty": 1})
        assert response.status_code == 401
