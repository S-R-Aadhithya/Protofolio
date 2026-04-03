from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import io
import zipfile
from ..models import db, User, Portfolio, PortfolioProject
from ..council.engine import CouncilEngine
from ..generator.renderer import PortfolioRenderer

portfolio_bp = Blueprint('portfolio', __name__)
engine = CouncilEngine()
renderer = PortfolioRenderer()


@portfolio_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json() or {}
    job_goal = data.get('job_goal', None)  # None = auto-infer from resume
    theme = data.get('theme', 'dark')

    result = engine.deliberate(user.id, job_goal)
    blueprint = result['blueprint']
    # Use the inferred/provided goal for DB storage
    effective_goal = result.get('inferred_goal', job_goal) or 'Auto-Generated Portfolio'
    blueprint['theme'] = theme

    new_portfolio = Portfolio(
        user_id=user.id,
        title=blueprint.get('tagline', f"Professional {job_goal} Portfolio"),
        target_role=job_goal,
        blueprint_json=json.dumps(blueprint)  # Save full blueprint for preview/export
    )
    db.session.add(new_portfolio)
    db.session.flush()

    projects = blueprint.get('projects', [])
    if isinstance(projects, list):
        for p_data in projects:
            p_name = p_data if isinstance(p_data, str) else p_data.get('name', 'Project')
            p_desc = p_data.get('description', '') if isinstance(p_data, dict) else ""
            db.session.add(PortfolioProject(
                portfolio_id=new_portfolio.id,
                name=p_name,
                description=p_desc
            ))

    db.session.commit()

    return jsonify({
        "status": "success",
        "portfolio_id": new_portfolio.id,
        "deliberation": result['deliberation'],
        "blueprint": blueprint
    }), 200

@portfolio_bp.route('/generate/stream', methods=['POST'])
@jwt_required()
def generate_stream():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json() or {}
    job_goal = data.get('job_goal', 'Software Engineer')
    theme = data.get('theme', 'dark')

    def event_stream():
        final_blueprint = None
        for chunk in engine.deliberate_stream(user.id, job_goal):
            yield chunk
            if chunk.startswith("data: ") and "complete" in chunk:
                try:
                    payload = json.loads(chunk[len("data: "):])
                    if payload.get("type") == "complete":
                        final_blueprint = payload.get("blueprint")
                except Exception:
                    pass

        if final_blueprint:
            final_blueprint['theme'] = theme
            new_portfolio = Portfolio(
                user_id=user.id,
                title=final_blueprint.get('tagline', f"Professional {job_goal} Portfolio"),
                target_role=job_goal
            )
            db.session.add(new_portfolio)
            db.session.flush()

            projects = final_blueprint.get('projects', [])
            if isinstance(projects, list):
                for p_data in projects:
                    p_name = p_data if isinstance(p_data, str) else p_data.get('name', 'Project')
                    p_desc = p_data.get('description', '') if isinstance(p_data, dict) else ""
                    db.session.add(PortfolioProject(
                        portfolio_id=new_portfolio.id,
                        name=p_name,
                        description=p_desc
                    ))
            db.session.commit()
            
            yield f"data: {json.dumps({'type': 'save_complete', 'portfolio_id': new_portfolio.id})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

@portfolio_bp.route('/list', methods=['GET'])
@jwt_required()
def list_portfolios():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    portfolios = Portfolio.query.filter_by(user_id=user.id).all()
    return jsonify([{
        "id": p.id,
        "title": p.title,
        "role": p.target_role,
        "created_at": p.created_at.isoformat()
    } for p in portfolios])


@portfolio_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    projects = PortfolioProject.query.filter_by(portfolio_id=id).all()
    return jsonify({
        "id": portfolio.id,
        "title": portfolio.title,
        "role": portfolio.target_role,
        "projects": [{"name": p.name, "description": p.description} for p in projects]
    })


@portfolio_bp.route('/<int:id>/preview', methods=['GET'])
@jwt_required()
def preview_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    projects = PortfolioProject.query.filter_by(portfolio_id=id).all()
    theme = request.args.get('theme', 'dark')

    # Restore full blueprint from saved JSON, fall back to minimal stub
    if portfolio.blueprint_json:
        blueprint = json.loads(portfolio.blueprint_json)
    else:
        blueprint = {
            "tagline": portfolio.title,
            "target_role": portfolio.target_role,
            "projects": [{"name": p.name, "description": p.description} for p in projects]
        }
    blueprint['theme'] = theme

    rendered = renderer.render(blueprint, theme=theme, portfolio_id=id)
    return jsonify({
        "portfolio_id": id,
        "theme": theme,
        "html": rendered["html"],
        "css": rendered["css"]
    }), 200

@portfolio_bp.route('/<int:id>/export', methods=['GET'])
@jwt_required()
def export_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    projects = PortfolioProject.query.filter_by(portfolio_id=id).all()
    theme = request.args.get('theme', 'dark')

    # Restore full blueprint from saved JSON
    if portfolio.blueprint_json:
        blueprint = json.loads(portfolio.blueprint_json)
    else:
        blueprint = {
            "tagline": portfolio.title,
            "target_role": portfolio.target_role,
            "projects": [{"name": p.name, "description": p.description} for p in projects]
        }
    blueprint['theme'] = theme

    rendered = renderer.render(blueprint, theme=theme, portfolio_id=id)
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        zf.writestr('index.html', rendered['html'])
        zf.writestr('styles.css', rendered['css'])
        
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'portfolio_{id}_{theme}.zip'
    )

@portfolio_bp.route('/<int:id>/analytics', methods=['POST'])
def record_analytics(id):
    portfolio = Portfolio.query.get_or_404(id)
    portfolio.views = (portfolio.views or 0) + 1
    db.session.commit()
    return jsonify({"status": "recorded", "views": portfolio.views}), 200
