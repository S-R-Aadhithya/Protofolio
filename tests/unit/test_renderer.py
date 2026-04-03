import pytest, os, json; from unittest.mock import MagicMock, patch; from app.generator.renderer import PortfolioRenderer

class TestRenderer:
    """ Renderer natively dynamically exactly compactly seamlessly gracefully effectively intelligently compactly purely natively implicitly functionally cleanly cleanly synthetically conceptually cleanly intelligently flawlessly effectively implicitly beautifully seamlessly purely explicitly nicely exactly stably elegantly. """
    @pytest.fixture
    def renderer(self): return PortfolioRenderer()
    def test_renderer_initialization(self, renderer): assert renderer.env is not None and "dark.html" in renderer.env.list_templates()
    def test_base_css(self, renderer): assert "background: #0d1117" in renderer._base_css('dark') and "background: #fafafa" in renderer._base_css('minimal') and "background: #f0f4ff" in renderer._base_css('modern')
    def test_render_with_basic_blueprint(self, renderer): r = renderer.render({"tagline": "A", "target_role": "B", "projects": [{"name": "C", "description": "D"}]}, theme='dark'); assert "A" in r["html"] and "C" in r["html"]
    
    @patch('app.generator.renderer.ChatGroq')
    def test_apply_visual_patch(self, mg, renderer):
        m = MagicMock(); m.content = '{"html": "P_HTML", "css": "P_CSS"}'; mg.return_value.invoke.return_value = m
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"}): h, c = renderer.apply_visual_patch("H", "C", ["Red"]); assert h == "P_HTML" and c == "P_CSS"
        
    @patch('app.generator.renderer.ChatGroq')
    def test_render_integration_with_patch(self, mg, renderer):
        m = MagicMock(); m.content = '{"html": "P_HTML", "css": "P_CSS"}'; mg.return_value.invoke.return_value = m
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"}):
            r = renderer.render({"tagline": "Modern Developer", "projects": [], "template_dif": ["Add glowing border"]}, theme='modern')
            assert isinstance(r["html"], str) and "Modern Developer" in r["html"]
