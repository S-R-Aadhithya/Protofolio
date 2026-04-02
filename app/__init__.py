import os
from flask import Flask
from flask_cors import CORS
from .models import db, bcrypt, jwt
from config import config_by_name

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:3000"]}})
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from flask import jsonify

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.error(f"JWT Invalid: {error}")
        return jsonify({"error": "Invalid token", "details": str(error)}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.error(f"JWT Expired: {jwt_payload}")
        return jsonify({"error": "Token has expired", "details": "Please log in again"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        app.logger.error(f"JWT Missing/Unauthorized: {error}")
        return jsonify({"error": "Authorization header missing", "details": str(error)}), 401

    with app.app_context():
        # Create database tables
        db.create_all()

    # Register blueprints
    from .api.auth import auth_bp, oauth
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    oauth.init_app(app)
    oauth.register(
        name='github',
        client_id=app.config.get('GITHUB_CLIENT_ID'),
        client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email read:user repo'},
    )
    
    from .api.ingest import ingest_bp
    from .api.portfolio import portfolio_bp
    from .api.deploy import deploy_bp
    
    app.register_blueprint(ingest_bp, url_prefix='/api/ingest')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(deploy_bp, url_prefix='/api/deploy')

    @app.route('/')
    def index():
        return {"status": "success", "message": "Protofolio API is running. Access the frontend at port 3000."}, 200

    return app
