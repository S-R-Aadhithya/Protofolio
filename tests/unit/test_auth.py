import pytest
import io


class TestLogin:
    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "test"})
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 401


class TestMe:
    def test_me_authenticated(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["logged_in_as"] == "test@example.com"

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestLogout:
    def test_logout(self, client, auth_headers):
        resp = client.post("/api/auth/logout", headers=auth_headers)
        assert resp.status_code == 200

    def test_logout_without_token(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401


class TestSandbox:
    def test_get_sandbox_empty(self, client, auth_headers):
        resp = client.get("/api/auth/sandbox", headers=auth_headers)
        assert resp.status_code in (200, 404)

    def test_save_and_get_sandbox(self, client, auth_headers, db, app):
        from app.models import User
        with app.app_context():
            if not User.query.filter_by(email="test@example.com").first():
                db.session.add(User(email="test@example.com"))
                db.session.commit()

        save_resp = client.post("/api/auth/sandbox", json={"code": "print('hello')"}, headers=auth_headers)
        assert save_resp.status_code == 200

        get_resp = client.get("/api/auth/sandbox", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.get_json()["code"] == "print('hello')"
