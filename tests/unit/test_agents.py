import pytest
from unittest.mock import MagicMock, patch
from app.council.agents import Chairman, TechLead, Designer, ProductManager

class TestAgents:
    @patch('app.council.agents.ChatGoogleGenerativeAI')
    @patch('app.council.agents.ChatGroq')
    def test_chairman_process_ingestion(self, mock_groq, mock_gemini):
        # Setup mock LLM response
        mock_response = MagicMock()
        mock_response.content = "Structured Summary: Experienced developer with Python and React."
        mock_gemini.return_value.invoke.return_value = mock_response

        chairman = Chairman(model="gemini-1.5-flash")
        result = chairman.process_ingestion("Raw resume text here", source_type="resume")
        
        assert "Structured Summary" in result
        assert "Experienced developer" in result

    @patch('app.council.agents.ChatGoogleGenerativeAI')
    @patch('app.council.agents.ChatGroq')
    def test_chairman_synthesize(self, mock_groq, mock_gemini):
        mock_response = MagicMock()
        mock_response.content = '{"tagline": "AI Expert", "target_role": "ML Engineer", "tech_stack": ["Python"], "projects": [], "layout_strategy": "clean", "template_dif": ["Add neon border"]}'
        mock_gemini.return_value.invoke.return_value = mock_response
        mock_groq.return_value.invoke.return_value = mock_response

        chairman = Chairman()
        result_json = chairman.synthesize("ML Engineer", "Deliberation details")
        
        assert "AI Expert" in result_json
        assert "template_dif" in result_json

    @patch('app.council.agents.ChatGoogleGenerativeAI')
    @patch('app.council.agents.ChatGroq')
    def test_base_agent_get_opinion(self, mock_groq, mock_gemini):
        mock_response = MagicMock()
        mock_response.content = "I think we should use React."
        mock_gemini.return_value.invoke.return_value = mock_response
        mock_groq.return_value.invoke.return_value = mock_response

        tech_lead = TechLead()
        opinion = tech_lead.get_opinion("User context", "Software Engineer")
        
        assert "React" in opinion
        assert tech_lead.name == "Dave"
