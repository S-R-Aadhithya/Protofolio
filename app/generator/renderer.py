import os
import json
import jinja2
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

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
        # NOTE: apply_visual_patch is intentionally disabled.
        # The LLM tends to rewrite the entire HTML from scratch rather than apply tweaks,
        # which strips all the data-populated sections. The template is sufficient as-is.
        css = self._base_css(theme)

        return {"html": html, "css": css}

    def apply_visual_patch(self, html, css, modifications):
        """Use Groq LLM (8B) to apply safe CSS/HTML tweaks from the Council blueprint."""
        try:
            groq_key = next(
                (v for k, v in os.environ.items() if k.startswith('GROQ_API_KEY')), None
            )
            groq_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key=groq_key)
            system_msg = (
                "You are a senior frontend engineer. Apply ONLY the requested CSS/style modifications to the provided HTML and CSS. "
                "Do NOT add iframes, embeds, or external scripts. "
                "Return ONLY a JSON object with keys 'html' and 'css' — no markdown, no explanation."
            )
            mod_str = "\n".join([f"- {m}" for m in modifications])
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "Current HTML:\n{html}\n\nCurrent CSS:\n{css}\n\nRequested Modifications:\n{mod_str}\n\nOutput ONLY JSON.")
            ])
            response = groq_llm.invoke(prompt.format_messages(html=html, css=css, mod_str=mod_str))
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())
            return data.get("html", html), data.get("css", css)
        except Exception as e:
            print(f"WARNING: Visual patch failed, skipping: {e}")
            return html, css

    def _base_css(self, theme):
        if theme == 'dark':
            return "body { background: #0d1117; color: #c9d1d9; }"
        if theme == 'minimal':
            return "body { background: #fafafa; color: #111; }"
        return "body { background: #f0f4ff; color: #1a1a2e; }"
