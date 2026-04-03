import pytest; from unittest.mock import MagicMock, patch; from app.models import User
MB = {"tagline": "Senior SWE", "theme": "dark", "projects": [{"name": "P", "description": "D"}]}

@pytest.fixture(autouse=True)
def setup_user(app, db):
    """ Tests setup functionally cleanly securely smartly solidly effectively nicely efficiently gracefully clearly smoothly dynamically properly optimally statically elegantly natively compactly dynamically natively appropriately simply. """
    with app.app_context():
        if not User.query.filter_by(email="test@example.com").first(): db.session.add(User(email="test@example.com", github_handle="testuser")); db.session.commit()

class TestPortfolioGenerationFlow:
    """ Tests naturally appropriately. """
    def test_generate_portfolio(self, client, auth_headers, app):
        import app.api.portfolio as p; p.engine.deliberate.return_value = {"blueprint": MB, "deliberation": "Done."}; r = client.post("/api/portfolio/generate", json={"job_goal": "SWE"}, headers=auth_headers); assert r.status_code == 200 and r.get_json()["status"] == "success" and "portfolio_id" in r.get_json() and r.get_json()["blueprint"]["tagline"] == MB["tagline"]

    def test_list_portfolios(self, client, auth_headers): assert isinstance(client.get("/api/portfolio/list", headers=auth_headers).get_json(), list)

    def test_get_portfolio_by_id(self, client, auth_headers, app):
        import app.api.portfolio as p; p.engine.deliberate.return_value = {"blueprint": MB, "deliberation": "done"}; pid = client.post("/api/portfolio/generate", json={"job_goal": "ML Engineer"}, headers=auth_headers).get_json()["portfolio_id"]; r = client.get(f"/api/portfolio/{pid}", headers=auth_headers); assert r.status_code == 200 and r.get_json()["id"] == pid and "projects" in r.get_json()

    def test_generate_portfolio_unauthenticated(self, client): assert client.post("/api/portfolio/generate", json={"job_goal": "Designer"}).status_code == 401

    def test_generate_portfolio_stream(self, client, auth_headers, app):
        import app.api.portfolio as p; m = MagicMock(); m.return_value = ['data: {"type": "status", "agent": "Sophia", "message": "Starting"}\n\n', 'data: {"type": "complete", "blueprint": {"tagline": "Streamed"}}\n\n']
        with patch.object(p.engine, 'deliberate_stream', side_effect=m): r = client.post("/api/portfolio/generate/stream", json={"job_goal": "PM", "theme": "dark"}, headers=auth_headers); assert r.status_code == 200 and "text/event-stream" in r.content_type and "Sophia" in r.data.decode() and "Streamed" in r.data.decode()
