from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    github_id = db.Column(db.String(120), unique=True)
    github_handle = db.Column(db.String(120))
    github_access_token = db.Column(db.String(255))
    google_id = db.Column(db.String(120), unique=True)
    linkedin_handle = db.Column(db.String(120))
    sandbox_code = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120))
    target_role = db.Column(db.String(120))
    blueprint_json = db.Column(db.Text)  # Full AI blueprint stored as JSON string
    github_repo_url = db.Column(db.String(255))
    github_pages_url = db.Column(db.String(255))
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class PortfolioProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    url = db.Column(db.String(255))

class MemoryChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    metadata_json = db.Column(db.Text) # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

