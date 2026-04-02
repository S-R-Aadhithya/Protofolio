import os
import jinja2
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load env vars for Groq
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tests', '.env'))

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
VALID_THEMES = {'dark', 'minimal', 'creative', 'professional', 'modern'}


class PortfolioRenderer:
    def __init__(self):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )

    def render(self, blueprint, theme='dark', portfolio_id=None):
        if theme not in VALID_THEMES:
            theme = 'dark'
        
        template = self.env.get_template(f'{theme}.html')
        html = template.render(
            portfolio_id=portfolio_id,
            tagline=blueprint.get('tagline', 'My Portfolio'),
            target_role=blueprint.get('target_role', ''),
            projects=blueprint.get('projects', []),
            tech_stack=blueprint.get('tech_stack', []),
            layout_strategy=blueprint.get('layout_strategy', ''),
        )
        css = self._base_css(theme)

        # Apply LLM-driven "dif" modifications if provided
        template_dif = blueprint.get('template_dif', [])
        if template_dif and os.getenv("GROQ_API_KEY"):
            html, css = self.apply_visual_patch(html, css, template_dif)

        return {"html": html, "css": css}

    def apply_visual_patch(self, html, css, modifications):
        """Use Groq to refine the HTML/CSS based on specific Council mods."""
        try:
            groq_llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.1)
            system_msg = "You are a senior frontend engineer. Update the provided HTML and CSS based on the requested modifications. Return only the updated HTML and CSS in a valid JSON format with keys 'html' and 'css'."
            
            mod_str = "\n".join([f"- {m}" for m in modifications])
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "Current HTML:\n{html}\n\nCurrent CSS:\n{css}\n\nRequested Modifications:\n{mod_str}\n\nOutput ONLY JSON.")
            ])
            
            response = groq_llm.invoke(prompt.format_messages(html=html, css=css, mod_str=mod_str))
            import json
            data = json.loads(response.content.strip("```json").strip("```"))
            return data.get("html", html), data.get("css", css)
        except Exception as e:
            print(f"WARNING: Groq visual patch failed: {e}")
            raise e

    def _base_css(self, theme):
        if theme == 'dark':
            return "body { background: #0d1117; color: #c9d1d9; }"
        if theme == 'minimal':
            return "body { background: #fafafa; color: #111; }"
        return "body { background: #f0f4ff; color: #1a1a2e; }"
