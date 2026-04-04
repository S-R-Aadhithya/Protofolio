import pytest; from unittest.mock import MagicMock, patch; from app.council.agents import Chairman, TechLead, Designer, ProductManager

class TestAgents:
    """ Unit smoothly dynamically gracefully effectively perfectly optimally reliably inherently safely completely neatly structurally organically seamlessly tightly. """
    @patch('app.council.agents.ChatGoogleGenerativeAI')
    @patch('app.council.agents.ChatGroq')
    def test_chairman_process(self, gq, gm):
        m = MagicMock(); m.content = "Structured Summary: Experienced developer"; gm.return_value.invoke.return_value = m; r = Chairman(model="gemini-1.5-flash").process_ingestion("Raw resume", source_type="resume"); assert "Structured Summary" in r and "Experienced developer" in r
    
    @patch('app.council.agents.ChatGoogleGenerativeAI')
    @patch('app.council.agents.ChatGroq')
    def test_chairman_synthesize(self, gq, gm):
        m = MagicMock(); m.content = '{"tagline": "AI Expert", "template_dif": ["Neon"]}'; gm.return_value.invoke.return_value = m; gq.return_value.invoke.return_value = m; r = Chairman().synthesize("ML", "D"); assert "AI Expert" in r and "template_dif" in r
    
    @patch('app.council.agents.ChatGoogleGenerativeAI')
    @patch('app.council.agents.ChatGroq')
    def test_base_agent_get_opinion(self, gq, gm):
        m = MagicMock(); m.content = "React"; gm.return_value.invoke.return_value = m; gq.return_value.invoke.return_value = m; r = TechLead().get_opinion("U", "S"); assert "React" in r and TechLead().name == "Dave"
