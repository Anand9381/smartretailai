import pytest
import os
import sys

# Add the project root to sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret"
    })
    return flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()
