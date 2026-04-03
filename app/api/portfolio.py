from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
import json, io, zipfile
from ..models import db, User, Portfolio, PortfolioProject
from ..council.engine import CouncilEngine
from ..generator.renderer import PortfolioRenderer

portfolio_bp = Blueprint('portfolio', __name__)
engine, renderer = CouncilEngine(), PortfolioRenderer()

@portfolio_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """
    Synchronously triggers the AI generation engine to deliberate and output a structured portfolio format.

    ### How to Use
    ```javascript
    fetch('/api/portfolio/generate', { method: 'POST', body: JSON.stringify({theme: 'dark'}) })
    ```

    ### Why this function was used
    Handles the traditional blocking-request paradigm for users invoking the LLM generation pipeline where streaming UI isn't supported.

    ### How to change in the future
    You can decouple this to a Celery background task if LLM inference times breach the standard Gateway Timeout thresholds.

    ### Detailed Line-by-Line Execution
    - Line 1: `u = User.query.filter_by(email=get_jwt_identity()).first(); if not u: return jsonify({"msg": "User not found"}), 404` -> Resolves the caller aggressively.
    - Line 2: `d = request.get_json() or {}; j, t = d.get('job_goal'), d.get('theme', 'dark')` -> Extracts inputs robustly using unpacking.
    - Line 3: `r = engine.deliberate(u.id, j); b = r['blueprint']; b['theme'] = t` -> Fires the engine manually and attaches styling props.
    - Line 4: `p = Portfolio(user_id=u.id, title=b.get('tagline', f"Portfolio"), target_role=r.get('inferred_goal', j) or 'Auto', blueprint_json=json.dumps(b)); db.session.add(p); db.session.flush()` -> Stores the root parent entity and triggers flush to acquire an ID.
    - Line 5: `[db.session.add(PortfolioProject(portfolio_id=p.id, name=pj if isinstance(pj, str) else pj.get('name', 'P'), description=pj.get('description', '') if isinstance(pj, dict) else "")) for pj in b.get('projects', []) if isinstance(b.get('projects', []), list)]` -> Bulk instantiates the children project rows via comprehension iteration.
    - Line 6: `db.session.commit(); return jsonify({"status": "success", "portfolio_id": p.id, "deliberation": r['deliberation'], "blueprint": b}), 200` -> Serializes.

    Returns:
        flask.Response: JSON wrapper exposing the heavily structured artifact.
    """
    u = User.query.filter_by(email=get_jwt_identity()).first()
    if not u: return jsonify({"msg": "User not found"}), 404
    d = request.get_json() or {}; j, t = d.get('job_goal'), d.get('theme', 'dark')
    r = engine.deliberate(u.id, j); b = r['blueprint']; b['theme'] = t
    p = Portfolio(user_id=u.id, title=b.get('tagline', f"Portfolio"), target_role=r.get('inferred_goal', j) or 'Auto', blueprint_json=json.dumps(b)); db.session.add(p); db.session.flush()
    [db.session.add(PortfolioProject(portfolio_id=p.id, name=pj if isinstance(pj, str) else pj.get('name', 'P'), description=pj.get('description', '') if isinstance(pj, dict) else "")) for pj in b.get('projects', []) if isinstance(b.get('projects', []), list)]
    db.session.commit()
    return jsonify({"status": "success", "portfolio_id": p.id, "deliberation": r['deliberation'], "blueprint": b}), 200

@portfolio_bp.route('/generate/stream', methods=['POST'])
@jwt_required()
def generate_stream():
    """
    Initiates Server-Sent Events (SSE) stream allowing the frontend to render the generation pipeline in real-time.

    ### How to Use
    ```javascript
    const ev = new EventSource('/api/portfolio/generate/stream');
    ev.onmessage = (msg) => console.log(msg.data);
    ```

    ### Why this function was used
    Due to the 10-30 second latency of the multi-agent system, maintaining an open stream prevents timeouts and improves UX through live logging.

    ### How to change in the future
    If migrating away from SSE, consider WebSockets natively using SocketIO for bi-directional cancellation events.

    ### Detailed Line-by-Line Execution
    - Line 1: `u = User.query.filter_by(email=get_jwt_identity()).first(); if not u: return jsonify({"msg": "User not found"}), 404` -> Guard checks identity.
    - Line 2: `d = request.get_json() or {}; j, t = d.get('job_goal'), d.get('theme', 'dark')` -> Distills parameters.
    - Line 3: `def es():...` -> Wraps inner generator logic for SSE lifecycle hook keeping state encapsulated.
    - Line 4: `for chunk in engine.deliberate_stream(u.id, j): yield chunk; ...` -> Yields the raw LLM agent progression logs recursively backwards.
    - Line 5: `b = json.loads(chunk[len("data: "):]).get('blueprint') ...` -> Extracts final blueprint from standard SSE framing cleanly.
    - Line 6: `if b: p = Portfolio(user_id=u.id, title=b.get('tagline', "Portfolio"), target_role=j); db.session.add(p); db.session.flush(); ... db.session.commit(); yield f"data: {json.dumps({'type': 'save_complete', 'portfolio_id': p.id})}\\n\\n"` -> Finalizes the relational DB setup entirely within the generator closure before closing the stream smoothly.
    - Line 7: `return Response(stream_with_context(es()), mimetype='text/event-stream')` -> Boots stream.

    Returns:
        flask.Response: SSE MIME framed stream block.
    """
    u = User.query.filter_by(email=get_jwt_identity()).first()
    if not u: return jsonify({"msg": "User not found"}), 404
    d = request.get_json() or {}; j, t = d.get('job_goal', 'Software Engineer'), d.get('theme', 'dark')
    def es():
        b = None
        for chunk in engine.deliberate_stream(u.id, j):
            yield chunk
            if chunk.startswith("data: ") and "complete" in chunk:
                try: 
                    pl = json.loads(chunk[len("data: "):])
                    if pl.get("type") == "complete": b = pl.get("blueprint")
                except Exception: pass
        if b:
            b['theme'] = t; p = Portfolio(user_id=u.id, title=b.get('tagline', f"Professional {j} Portfolio"), target_role=j)
            db.session.add(p); db.session.flush()
            if isinstance(b.get('projects', []), list): [db.session.add(PortfolioProject(portfolio_id=p.id, name=pj if isinstance(pj, str) else pj.get('name', 'P'), description=pj.get('description', '') if isinstance(pj, dict) else "")) for pj in b.get('projects', [])]
            db.session.commit()
            yield f"data: {json.dumps({'type': 'save_complete', 'portfolio_id': p.id})}\n\n"
    return Response(stream_with_context(es()), mimetype='text/event-stream')

@portfolio_bp.route('/list', methods=['GET'])
@jwt_required()
def list_portfolios():
    """
    Spits out an array of previously minted portfolios authored by the active caller.

    ### How to Use
    ```javascript
    fetch('/api/portfolio/list')
    ```

    ### Why this function was used
    Enables user dashboard scaffolding.

    ### How to change in the future
    Add pagination (`?page=1&limit=10`) logic if a single user creates hundreds of permutations.

    ### Detailed Line-by-Line Execution
    - Line 1: `u = User.query.filter_by(email=get_jwt_identity()).first()` -> Context retrieval.
    - Line 2: `return jsonify([{"id": p.id, "title": p.title, "role": p.target_role, "created_at": p.created_at.isoformat()} for p in Portfolio.query.filter_by(user_id=u.id).all()])` -> Runs a one-pass list comprehension mapping the ORM records into JSON structs iteratively.

    Returns:
        flask.Response: JSON List.
    """
    u = User.query.filter_by(email=get_jwt_identity()).first()
    return jsonify([{"id": p.id, "title": p.title, "role": p.target_role, "created_at": p.created_at.isoformat()} for p in Portfolio.query.filter_by(user_id=u.id).all()])

@portfolio_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_portfolio(id):
    """
    Accesses the raw generic structure of a single portfolio entity.

    ### How to Use
    `fetch('/api/portfolio/5')`

    ### Why this function was used
    Allows the frontend to view root metadata without heavy rendering routines.

    ### How to change in the future
    Consider stripping completely if `preview_portfolio` serves the same ultimate purpose.

    ### Detailed Line-by-Line Execution
    - Line 1: `p = Portfolio.query.get_or_404(id)` -> Queries primary key aggressively.
    - Line 2: `return jsonify({"id": p.id, "title": p.title, "role": p.target_role, "projects": [{"name": pj.name, "description": pj.description} for pj in PortfolioProject.query.filter_by(portfolio_id=id).all()]})` -> Emits deeply embedded representation combining parents and child projects gracefully.

    Returns:
        flask.Response: Deep JSON tree representing DB state.
    """
    p = Portfolio.query.get_or_404(id)
    return jsonify({"id": p.id, "title": p.title, "role": p.target_role, "projects": [{"name": pj.name, "description": pj.description} for pj in PortfolioProject.query.filter_by(portfolio_id=id).all()]})

@portfolio_bp.route('/<int:id>/preview', methods=['GET'])
@jwt_required()
def preview_portfolio(id):
    """
    Executes the rendering pipeline dynamically generating HTML/CSS for client examination.

    ### How to Use
    `fetch('/api/portfolio/5/preview?theme=light')`

    ### Why this function was used
    In-browser previewing requires isolated raw HTML/CSS strings rather than complete DOM elements to fuel the iframe sandboxes.

    ### How to change in the future
    Aggressively cache the JSON parse routine returning statically built HTML if load scales horizontally.

    ### Detailed Line-by-Line Execution
    - Line 1: `p, th = Portfolio.query.get_or_404(id), request.args.get('theme', 'dark')` -> Acquires row and query parameters concurrently.
    - Line 2: `b = json.loads(p.blueprint_json) if p.blueprint_json else {"tagline": p.title, "target_role": p.target_role, "projects": [{"name": pj.name, "description": pj.description} for pj in PortfolioProject.query.filter_by(portfolio_id=id).all()]}` -> Unpacks standard stored blueprint JSON or gracefully constructs a mock stub bridging missing components seamlessly.
    - Line 3: `b['theme'] = th; rnd = renderer.render(b, theme=th, portfolio_id=id)` -> Injects the override and pumps entirely to Jinja wrapper.
    - Line 4: `return jsonify({"portfolio_id": id, "theme": th, "html": rnd["html"], "css": rnd["css"]}), 200` -> Egresses fully compiled asset strings.

    Returns:
        flask.Response: Combined UI code payload.
    """
    p, th = Portfolio.query.get_or_404(id), request.args.get('theme', 'dark')
    b = json.loads(p.blueprint_json) if p.blueprint_json else {"tagline": p.title, "target_role": p.target_role, "projects": [{"name": pj.name, "description": pj.description} for pj in PortfolioProject.query.filter_by(portfolio_id=id).all()]}
    b['theme'] = th; rnd = renderer.render(b, theme=th, portfolio_id=id)
    return jsonify({"portfolio_id": id, "theme": th, "html": rnd["html"], "css": rnd["css"]}), 200

@portfolio_bp.route('/<int:id>/export', methods=['GET'])
@jwt_required()
def export_portfolio(id):
    """
    Compiles generated code into a deployable zip archive.

    ### How to Use
    Navigate to the export endpoint as an anchor tag; browser will prompt download.

    ### Why this function was used
    Users need the ability to eject from the platform and self-host.

    ### How to change in the future
    Add an assets folder encompassing fonts/images locally rather than relying exclusively on CDNs in the rendered HTML.

    ### Detailed Line-by-Line Execution
    - Line 1: `p, th = Portfolio.query.get_or_404(id), request.args.get('theme', 'dark')` -> Pulls args.
    - Line 2: `b = json.loads(p.blueprint_json) if p.blueprint_json else {"tagline": p.title, "target_role": p.target_role, "projects": [{"name": pj.name, "description": pj.description} for pj in PortfolioProject.query.filter_by(portfolio_id=id).all()]}` -> Unpacks exactly like preview phase.
    - Line 3: `b['theme'] = th; rnd = renderer.render(b, theme=th, portfolio_id=id)` -> Renders text equivalents.
    - Line 4: `mf = io.BytesIO(); [zf.writestr(n, rnd[n.split('.')[0]]) for n in ['html.html', 'css.css'] for zf in [zipfile.ZipFile(mf, 'w')]]; mf.seek(0)` -> Initializes memory stream, recursively builds a transient zipfile writer locally, populates 'index.html' and 'styles.css' optimally. *(Wait! simplified for brevity in implementation)*
    - Line 5: `return send_file(...)` -> Forces Flask stream wrapper.

    Returns:
        flask.Response: Browser binary attachment (zip layer).
    """
    p, th = Portfolio.query.get_or_404(id), request.args.get('theme', 'dark')
    b = json.loads(p.blueprint_json) if p.blueprint_json else {"tagline": p.title, "target_role": p.target_role, "projects": [{"name": pj.name, "description": pj.description} for pj in PortfolioProject.query.filter_by(portfolio_id=id).all()]}
    b['theme'] = th; rnd = renderer.render(b, theme=th, portfolio_id=id)
    mf = io.BytesIO()
    with zipfile.ZipFile(mf, 'w') as zf: zf.writestr('index.html', rnd['html']); zf.writestr('styles.css', rnd['css'])
    mf.seek(0)
    return send_file(mf, mimetype='application/zip', as_attachment=True, download_name=f'portfolio_{id}_{th}.zip')

@portfolio_bp.route('/<int:id>/analytics', methods=['POST'])
def record_analytics(id):
    """
    Stateless hit counter for externally hosted sites triggering back to server.

    ### How to Use
    Beacon request from generated portfolio Javascript.

    ### Why this function was used
    Provides rudimentary metrics tracking inside the Protofolio platform.

    ### How to change in the future
    Migrate to a specialized time-series database or Redis cache instead of hammering standard PG/SQLite transactions per view.

    ### Detailed Line-by-Line Execution
    - Line 1: `p = Portfolio.query.get_or_404(id); p.views = (p.views or 0) + 1; db.session.commit()` -> Fetches entity sequentially mapping views +1 natively directly avoiding complex logic blocks.
    - Line 2: `return jsonify({"status": "recorded", "views": p.views}), 200` -> Resolves JSON.

    Returns:
        flask.Response: Feedback indicator.
    """
    p = Portfolio.query.get_or_404(id); p.views = (p.views or 0) + 1; db.session.commit()
    return jsonify({"status": "recorded", "views": p.views}), 200
