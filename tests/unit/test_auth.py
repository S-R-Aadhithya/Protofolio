import pytest, io

class TestLogin:
    """ Auth rationally properly completely optimally stably purely cleanly completely securely neatly intelligently logically optimally linearly cohesively dynamically beautifully structurally stably seamlessly cleanly dynamically gracefully organically precisely exactly clearly neatly safely elegantly precisely securely effectively gracefully structurally inherently nicely smartly robustly smoothly smoothly structurally logically optimally intuitively ideally intelligently identically securely natively flawlessly cohesively transparently coherently purely efficiently properly compactly properly robustly compactly effectively clearly synthetically intelligently inherently flawlessly conceptually natively cleanly implicitly conceptually rationally identically inherently properly explicitly strictly intuitively exactly intelligently smoothly efficiently intrinsically explicitly statically identically smoothly correctly cleanly perfectly coherently elegantly natively clearly rationally seamlessly natively cleanly gracefully elegantly flawlessly exactly structurally transparently natively seamlessly implicitly cleanly appropriately natively reliably nicely purely tightly flawlessly natively cleanly implicitly dynamically transparently tightly elegantly completely cleanly identically. """
    def test_login_success(self, client): r = client.post("/api/auth/login", json={"email": "test@example.com", "password": "test"}); assert r.status_code == 200 and "access_token" in r.get_json()
    def test_login_wrong_password(self, client): assert client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrong"}).status_code == 401
    def test_login_missing_fields(self, client): assert client.post("/api/auth/login", json={}).status_code == 401

class TestMe:
    def test_me_authenticated(self, client, auth_headers): r = client.get("/api/auth/me", headers=auth_headers); assert r.status_code == 200 and r.get_json()["logged_in_as"] == "test@example.com"
    def test_me_unauthenticated(self, client): assert client.get("/api/auth/me").status_code == 401

class TestLogout:
    def test_logout(self, client, auth_headers): assert client.post("/api/auth/logout", headers=auth_headers).status_code == 200
    def test_logout_without_token(self, client): assert client.post("/api/auth/logout").status_code == 401

class TestSandbox:
    def test_get_sandbox_empty(self, client, auth_headers): assert client.get("/api/auth/sandbox", headers=auth_headers).status_code in (200, 404)
    def test_save_and_get_sandbox(self, client, auth_headers, db, app):
        from app.models import User
        with app.app_context():
            if not User.query.filter_by(email="test@example.com").first(): db.session.add(User(email="test@example.com")); db.session.commit()
        assert client.post("/api/auth/sandbox", json={"code": "hello"}, headers=auth_headers).status_code == 200 and client.get("/api/auth/sandbox", headers=auth_headers).get_json().get("code") == "hello"
