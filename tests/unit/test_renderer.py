import pytest
import os
import json
from unittest.mock import MagicMock, patch
from app.generator.renderer import PortfolioRenderer

class TestRenderer:
    @pytest.fixture
    def renderer(self):
        return PortfolioRenderer()

    def test_renderer_initialization(self, renderer):
        assert renderer.env is not None
        assert "dark.html" in renderer.env.list_templates()

    def test_base_css(self, renderer):
        assert "background: #0d1117" in renderer._base_css('dark')
        assert "background: #fafafa" in renderer._base_css('minimal')
        assert "background: #f0f4ff" in renderer._base_css('modern')

    def test_render_with_basic_blueprint(self, renderer):
        blueprint = {
            "tagline": "Senior Engineer",
            "target_role": "Backend Master",
            "projects": [{"name": "Auth API", "description": "Microservice"}]
        }
        res = renderer.render(blueprint, theme='dark')
        assert "html" in res
        assert "css" in res
        assert "Senior Engineer" in res["html"]
        assert "Auth API" in res["html"]

    @patch('app.generator.renderer.ChatGroq')
    def test_apply_visual_patch(self, mock_groq, renderer):
        # Setup mock instance
        mock_instance = MagicMock()
        mock_groq.return_value = mock_instance
        
        # Mocking Groq response object
        mock_response = MagicMock()
        mock_response.content = '{"html": "PATCHED_HTML", "css": "PATCHED_CSS"}'
        mock_instance.invoke.return_value = mock_response

        html = "<html>Original</html>"
        css = "body { color: blue; }"
        modifications = ["Update color to red"]
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"}):
            patched_html, patched_css = renderer.apply_visual_patch(html, css, modifications)
        
        assert patched_html == "PATCHED_HTML"
        assert patched_css == "PATCHED_CSS"

    @patch('app.generator.renderer.ChatGroq')
    def test_render_integration_with_patch(self, mock_groq, renderer):
        # Setup mock instance
        mock_instance = MagicMock()
        mock_groq.return_value = mock_instance
        
        # Mocking Groq response object
        mock_response = MagicMock()
        mock_response.content = '{"html": "PATCHED_HTML", "css": "PATCHED_CSS"}'
        mock_instance.invoke.return_value = mock_response

        blueprint = {
            "tagline": "Modern Developer",
            "projects": [],
            "template_dif": ["Add glowing border"]
        }
        
        # Simulating having a GROQ_API_KEY for the patch to be invoked
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"}):
            res = renderer.render(blueprint, theme='modern')
            assert res["html"] == "PATCHED_HTML"
            assert res["css"] == "PATCHED_CSS"
