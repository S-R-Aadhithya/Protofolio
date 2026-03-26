import sys
import os
import pytest
from unittest.mock import MagicMock

# Set dummy key for tests to avoid pydantic validation errors in LangChain
os.environ.setdefault("GEMINI_API_KEY", "your_gemini_api_key_dummy")


from app import create_app
from app.models import db as _db

@pytest.fixture(scope="session")
def app():
    _app = create_app("test")
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    _app.config["WTF_CSRF_ENABLED"] = False
    with _app.app_context():
        _db.create_all()
        # Mocking components that interact with external services or complex state
        import app.api.ingest as ingest_module
        import app.api.portfolio as portfolio_module
        ingest_module.memory = MagicMock()
        portfolio_module.engine = MagicMock()
        yield _app
        _db.drop_all()

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()

@pytest.fixture(scope="function")
def auth_token(client):
    resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "test"})
    return resp.get_json()["access_token"]

@pytest.fixture(scope="function")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
