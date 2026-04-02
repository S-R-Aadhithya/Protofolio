import os
import jinja2


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
VALID_THEMES = {'dark', 'minimal', 'creative'}


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
        return {"html": html, "css": css}

    def _base_css(self, theme):
        if theme == 'dark':
            return "body { background: #0d1117; color: #c9d1d9; }"
        if theme == 'minimal':
            return "body { background: #fafafa; color: #111; }"
        return "body { background: #f0f4ff; color: #1a1a2e; }"
