from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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
    job_goal = data.get('job_goal', 'Software Engineer')
    theme = data.get('theme', 'dark')

    result = engine.deliberate(user.id, job_goal)
    blueprint = result['blueprint']
    blueprint['theme'] = theme

    new_portfolio = Portfolio(
        user_id=user.id,
        title=blueprint.get('tagline', f"Professional {job_goal} Portfolio"),
        target_role=job_goal
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

    blueprint = {
        "tagline": portfolio.title,
        "target_role": portfolio.target_role,
        "theme": theme,
        "projects": [{"name": p.name, "description": p.description} for p in projects]
    }

    rendered = renderer.render(blueprint, theme=theme)
    return jsonify({
        "portfolio_id": id,
        "theme": theme,
        "html": rendered["html"],
        "css": rendered["css"]
    }), 200
