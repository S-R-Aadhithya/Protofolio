import jinja2

class PortfolioRenderer:
    def __init__(self):
        # We'd ideally load Bootstrap 5 templates bundled with the backend
        self.env = jinja2.Environment()

    def render(self, blueprint):
        # Mocking actual jinja file rendering
        html = self._render_html(blueprint)
        css = self._render_css(blueprint.get("design", {}))
        return {
            "html": html,
            "css": css
        }

    def _render_html(self, blueprint):
        # The Architect blueprint comes in and guides the layout
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="style.css">
            <title>Portfolio - {{ blueprint.content.skills[0] }} Specialist</title>
        </head>
        <body class="bg-{{ blueprint.design.theme }}">
            <div class="container text-center py-5">
                <h1>Hello, I'm a developer</h1>
                <p>Welcome to my protofolio!</p>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        template = self.env.from_string(template_str)
        return template.render(blueprint=blueprint)

    def _render_css(self, design_blueprint):
        primary = design_blueprint.get("primary_color", "#000")
        return f"""
        body {{
            font-family: 'Inter', sans-serif;
        }}
        .bg-dark {{ color: #ffffff; background-color: #1a1a1a; }}
        h1 {{ color: {primary}; }}
        """
