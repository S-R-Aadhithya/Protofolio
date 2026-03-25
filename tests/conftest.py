import sys
import pytest
from unittest.mock import MagicMock

_STUB_MODULES = [
    "mem0", "mem0.memory",
    "langchain_openai",
    "langchain_core", "langchain_core.prompts", "langchain_core.messages",
    "langchain_core.language_models", "langchain_core.outputs",
    "langchain", "langchain.schema", "langchain.prompts", "langchain.chat_models",
    "openai",
    "anthropic",
    "github", "github.GithubException",
    "PyPDF2",
]
for _mod in _STUB_MODULES:
    sys.modules.setdefault(_mod, MagicMock())

from app import create_app
from app.models import db as _db


@pytest.fixture(scope="session")
def app():
    _app = create_app("test")
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    _app.config["WTF_CSRF_ENABLED"] = False
    with _app.app_context():
        _db.create_all()
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
