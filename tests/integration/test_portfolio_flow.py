import pytest
from app.models import User


MOCK_BLUEPRINT = {
    "tagline": "Senior Software Engineer Portfolio",
    "theme": "dark",
    "projects": [{"name": "Protofolio", "description": "Agentic RAG portfolio generator"}]
}


@pytest.fixture(autouse=True)
def setup_user(app, db):
    with app.app_context():
        if not User.query.filter_by(email="test@example.com").first():
            db.session.add(User(email="test@example.com", github_handle="testuser"))
            db.session.commit()


class TestPortfolioGenerationFlow:
    def test_generate_portfolio(self, client, auth_headers, app):
        import app.api.portfolio as portfolio_module
        portfolio_module.engine.deliberate.return_value = {
            "blueprint": MOCK_BLUEPRINT,
            "deliberation": "Agents agreed."
        }
        resp = client.post("/api/portfolio/generate", json={"job_goal": "Software Engineer"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "portfolio_id" in data
        assert data["blueprint"]["tagline"] == MOCK_BLUEPRINT["tagline"]

    def test_list_portfolios(self, client, auth_headers):
        resp = client.get("/api/portfolio/list", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_get_portfolio_by_id(self, client, auth_headers, app):
        import app.api.portfolio as portfolio_module
        portfolio_module.engine.deliberate.return_value = {
            "blueprint": MOCK_BLUEPRINT,
            "deliberation": "done"
        }
        gen_resp = client.post("/api/portfolio/generate", json={"job_goal": "ML Engineer"}, headers=auth_headers)
        portfolio_id = gen_resp.get_json()["portfolio_id"]

        get_resp = client.get(f"/api/portfolio/{portfolio_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.get_json()["id"] == portfolio_id
        assert "projects" in get_resp.get_json()

    def test_generate_portfolio_unauthenticated(self, client):
        resp = client.post("/api/portfolio/generate", json={"job_goal": "Designer"})
        assert resp.status_code == 401
