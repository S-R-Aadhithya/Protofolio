from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import db, User

auth_bp = Blueprint('proto_auth', __name__)

from authlib.integrations.flask_client import OAuth

oauth = OAuth()

@auth_bp.route('/github/login')
def github_login():
    redirect_uri = 'http://localhost:5001/api/auth/github/callback'
    return oauth.github.authorize_redirect(redirect_uri)

@auth_bp.route('/github/callback', methods=['GET'])
def github_callback():
    token = oauth.github.authorize_access_token()
    resp = oauth.github.get('user')
    profile = resp.json()
    
    github_id = str(profile['id'])
    email = profile.get('email')
    
    if not email:
        email_resp = oauth.github.get('user/emails')
        emails = email_resp.json()
        for e in emails:
            if e.get('primary') and e.get('verified'):
                email = e.get('email')
                break
        
        if not email and emails.__class__ == list and len(emails) > 0:
            email = emails[0].get('email')
            
    if not email:
        email = f"{profile['login']}@github.local"
    
    user = User.query.filter_by(github_id=github_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.github_id = github_id
            user.github_handle = profile['login']
            user.github_access_token = token.get('access_token')
        else:
            user = User(
                email=email,
                github_id=github_id,
                github_handle=profile['login'],
                github_access_token=token.get('access_token')
            )
            db.session.add(user)
    else:
        user.github_access_token = token.get('access_token')
        
    db.session.commit()

    access_token = create_access_token(identity=user.email)
    frontend_url = 'http://localhost:5173/setup'
    return redirect(f"{frontend_url}?token={access_token}&user={user.github_handle}")

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if email != 'test@example.com' or password != 'test':
        return jsonify({"msg": "Bad username or password"}), 401
    
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@auth_bp.route('/sandbox', methods=['GET'])
@jwt_required()
def get_sandbox():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"code": user.sandbox_code or ""}), 200

@auth_bp.route('/sandbox', methods=['POST'])
@jwt_required()
def save_sandbox():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    code = data.get('code', '')
    user.sandbox_code = code
    db.session.commit()
    return jsonify({"message": "Sandbox code saved successfully"}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"msg": "Successfully logged out"}), 200
