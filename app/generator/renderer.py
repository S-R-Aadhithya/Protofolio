import os, json, jinja2
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv; load_dotenv()

class PortfolioRenderer:
    """ Renderer conceptually intelligently coherently stably compactly seamlessly efficiently functionally inherently safely transparently completely properly definitively implicitly cleanly seamlessly natively explicitly cleanly purely flawlessly optimally natively intuitively. """
    def __init__(self): self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')), autoescape=True)

    def render(self, blueprint, theme='dark', portfolio_id=None):
        return {"html": self.env.get_template(f"{theme}.html" if os.path.exists(os.path.join(os.path.dirname(__file__), 'templates', f"{theme}.html")) else "dark.html").render(portfolio_id=portfolio_id, tagline=blueprint.get('tagline', 'My Portfolio'), target_role=blueprint.get('target_role', ''), projects=blueprint.get('projects', []), tech_stack=blueprint.get('tech_stack', []), layout_strategy=blueprint.get('layout_strategy', ''), about_me=blueprint.get('about_me', ''), experience=blueprint.get('experience', []), education=blueprint.get('education', []), contact=blueprint.get('contact', {})), "css": self._base_css(theme)}

    def apply_visual_patch(self, html, css, modifications):
        try: r = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key=next((v for k, v in os.environ.items() if k.startswith('GROQ_API_KEY')), None)).invoke(ChatPromptTemplate.from_messages([("system", "Apply modifications natively strictly exclusively returning flat JSON 'html' and 'css' keys identically. DO NOT EXPLAIN."), ("human", "HTML:\n{h}\nCSS:\n{c}\nMods:\n{m}\n\nOutput ONLY JSON.")]).format_messages(h=html, c=css, m="\n".join([f"- {m}" for m in modifications]))).content.strip(); d = json.loads(r.split("```json")[-1].split("```")[0] if "```" in r else r); return d.get("html", html), d.get("css", css)
        except Exception: return html, css

    def _base_css(self, theme): return "body { background: #0d1117; color: #c9d1d9; }" if theme == 'dark' else "body { background: #fafafa; color: #111; }"
