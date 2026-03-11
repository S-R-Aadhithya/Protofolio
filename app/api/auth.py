from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import db, User

auth_bp = Blueprint('auth', __name__)

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
    
    # If the user's email is private, GitHub won't return it in the main profile. 
    # We must explicitly fetch it from the /user/emails endpoint using the same access token.
    if not email:
        email_resp = oauth.github.get('user/emails')
        emails = email_resp.json()
        # Find the primary, verified email
        for e in emails:
            if e.get('primary') and e.get('verified'):
                email = e.get('email')
                break
        
        # Absolute fallback if no verified primary email is found
        if not email and emails.__class__ == list and len(emails) > 0:
            email = emails[0].get('email')
            
    # Final fallback if the API returns absolutely no emails (rare edge case)
    if not email:
        email = f"{profile['login']}@github.local"
    
    user = User.query.filter_by(github_id=github_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            # Link existing account to GitHub
            user.github_id = github_id
            user.github_handle = profile['login']
            user.github_access_token = token.get('access_token')
        else:
            # Create new user
            user = User(
                email=email,
                github_id=github_id,
                github_handle=profile['login'],
                github_access_token=token.get('access_token')
            )
            db.session.add(user)
    else:
        # Update existing user's token
        user.github_access_token = token.get('access_token')
        
    db.session.commit()

    access_token = create_access_token(identity=user.email)
    frontend_url = 'http://localhost:5173/setup'
    from flask import redirect
    return redirect(f"{frontend_url}?token={access_token}&user={user.github_handle}")

@auth_bp.route('/google/login')
def google_login():
    redirect_uri = 'http://localhost:5001/api/auth/google/callback'
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    token = oauth.google.authorize_access_token()
    # For OpenID Connect, the userinfo is usually inside the token or can be fetched
    profile = token.get('userinfo')
    if not profile:
        profile = oauth.google.userinfo()
        
    google_id = str(profile['sub']) # 'sub' is the unique ID in OIDC
    email = profile.get('email')
    
    # Fallback to a dummy email if none provided (rare for Google)
    if not email:
        email = f"{profile.get('name', 'user').replace(' ', '_')}@google.local"
        
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            # Link existing account to Google
            user.google_id = google_id
        else:
            # Create new user
            user = User(
                email=email,
                google_id=google_id,
                # For google we don't naturally have a github handle, but let's use name or email prefix as a placeholder handle 
                github_handle=profile.get('name', email.split('@')[0]) 
            )
            db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.email)
    frontend_url = 'http://localhost:5173/setup'
    from flask import redirect
    return redirect(f"{frontend_url}?token={access_token}&user={user.github_handle}")

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    # Validate against DB dummy for now
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
