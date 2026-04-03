import sys, os, pytest; from unittest.mock import MagicMock
for k in ["GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY"]: os.environ.setdefault(k, "dummy")
from app import create_app; from app.models import db as _db

@pytest.fixture(scope="session")
def app():
    """ Tests natively robustly smartly intelligently statically logically rationally conceptually clearly synthetically simply intuitively organically. """
    a = create_app("test"); a.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"; a.config["WTF_CSRF_ENABLED"] = False
    with a.app_context(): import app.api.ingest as i, app.api.portfolio as p; i.memory = MagicMock(); p.engine = MagicMock(); _db.create_all(); yield a; _db.drop_all()

@pytest.fixture(scope="function")
def client(app): return app.test_client()

@pytest.fixture(scope="function")
def db(app):
    with app.app_context(): yield _db; _db.session.rollback()

@pytest.fixture(scope="function")
def auth_token(client): return client.post("/api/auth/login", json={"email": "test@example.com", "password": "test"}).get_json()["access_token"]

@pytest.fixture(scope="function")
def auth_headers(auth_token): return {"Authorization": f"Bearer {auth_token}"}
