from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from authlib.integrations.flask_client import OAuth
from ..models import db, User

auth_bp = Blueprint('proto_auth', __name__)
oauth = OAuth()

@auth_bp.route('/github/login')
def github_login():
    """
    Initiates the GitHub OAuth login flow.

    ### How to Use
    ```python
    # Navigate to this route in the UI or fetch to trigger redirect.
    window.location.href = '/api/auth/github/login'
    ```

    ### Why this function was used
    Provides standard entry point for OAuth to seamlessly authenticate users against GitHub.

    ### How to change in the future
    You can parameterize `redirect_uri` using `os.getenv` for multi-environment deployments.

    ### Detailed Line-by-Line Execution
    - Line 1: `return oauth.github.authorize_redirect('http://localhost:5001/api/auth/github/callback')` -> Instructs the OAuth client to construct a GitHub authorization URL and immediately returns a Flask redirect.

    Returns:
        werkzeug.wrappers.Response: An HTTP redirect to GitHub.
    """
    return oauth.github.authorize_redirect('http://localhost:5001/api/auth/github/callback')

@auth_bp.route('/github/callback', methods=['GET'])
def github_callback():
    """
    Handles the redirection back from GitHub, fetches user profile, and issues JWT tokens.

    ### How to Use
    This route is called automatically by GitHub after the user authorizes the app. Do not call it manually.

    ### Why this function was used
    Required by OAuth 2.0 specs to exchange the authorization code for an access token and extract the user's identity to create or update their local account record.

    ### How to change in the future
    If integrating an alternative provider (e.g., Google), duplicate this callback logic adjusting the endpoint names and the profile JSON structure.

    ### Detailed Line-by-Line Execution
    - Line 1: `token = oauth.github.authorize_access_token()` -> Exchanges the URL code for an OAuth access token.
    - Line 2: `p = oauth.github.get('user').json()` -> Fetches base profile payload from GitHub.
    - Line 3: `email = p.get('email') or next((e['email'] for e in oauth.github.get('user/emails').json() if e.get('primary')), f"{p['login']}@github.local")` -> Falls back to searching the /user/emails endpoint if email is private, or generates a local fake email as a last resort.
    - Line 4: `u = User.query.filter_by(github_id=str(p['id'])).first() or User.query.filter_by(email=email).first() or User(email=email)` -> Attempts to find an existing user by ID or email, otherwise prepares a new record.
    - Line 5: `u.github_id, u.github_handle, u.github_access_token = str(p['id']), p['login'], token.get('access_token')` -> Mass updates the user variables to match the latest GitHub data.
    - Line 6: `db.session.add(u); db.session.commit()` -> Commits the updated or new user to the SQL database.
    - Line 7: `return redirect(f"http://localhost:5173/setup?token={create_access_token(identity=u.email)}&user={u.github_handle}")` -> Redirects the client to the frontend, passing the newly minted JWT and username.

    Returns:
        werkzeug.wrappers.Response: Redirect containing JWT.
    """
    token = oauth.github.authorize_access_token()
    p = oauth.github.get('user').json()
    email = p.get('email') or next((e['email'] for e in oauth.github.get('user/emails').json() if e.get('primary')), f"{p['login']}@github.local")
    
    u = User.query.filter_by(github_id=str(p['id'])).first() or User.query.filter_by(email=email).first() or User(email=email)
    u.github_id, u.github_handle, u.github_access_token = str(p['id']), p['login'], token.get('access_token')
    
    db.session.add(u)
    db.session.commit()
    return redirect(f"http://localhost:5173/setup?token={create_access_token(identity=u.email)}&user={u.github_handle}")

@auth_bp.route('/dev-login', methods=['GET'])
def dev_login():
    """
    Test environment backdoor for auto-login without user interaction.

    ### How to Use
    ```python
    fetch('/api/auth/dev-login')
    ```

    ### Why this function was used
    Allows end-to-end automated testing to bypass OAuth browser interactions.

    ### How to change in the future
    Delete or comment this out in production environments to avoid massive security holes.

    ### Detailed Line-by-Line Execution
    - Line 1: `u = User.query.filter_by(email="agent-test@example.com").first() or User(email="agent-test@example.com", github_id="mock_id", github_handle="agent-tester", github_access_token="mock_token")` -> Retrieves or seeds a mock user.
    - Line 2: `db.session.add(u); db.session.commit()` -> Assures the mock user exists in the database.
    - Line 3: `return redirect(f"http://localhost:5173/setup?token={create_access_token(identity=u.email)}&user={u.github_handle}")` -> Mints a JWT and redirects to setup.

    Returns:
        werkzeug.wrappers.Response: Redirect containing JWT.
    """
    u = User.query.filter_by(email="agent-test@example.com").first() or User(email="agent-test@example.com", github_id="mock_id", github_handle="agent-tester", github_access_token="mock_token")
    db.session.add(u)
    db.session.commit()
    return redirect(f"http://localhost:5173/setup?token={create_access_token(identity=u.email)}&user={u.github_handle}")

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Provides standard JSON-based login for non-OAuth mock authentication.

    ### How to Use
    ```javascript
    fetch('/api/auth/login', { method: 'POST', body: JSON.stringify({email:'test@example.com', password:'test'}) })
    ```

    ### Why this function was used
    Offers a fallback to standard credentials if OAuth is broken or purely for simple UI testing.

    ### How to change in the future
    Implement actual password hashing verification (like bcrypt) if keeping this endpoint for real use.

    ### Detailed Line-by-Line Execution
    - Line 1: `d = request.json or {}` -> Extracts raw JSON body.
    - Line 2: `if d.get('email') != 'test@example.com' or d.get('password') != 'test': return jsonify({"msg": "Bad username or password"}), 401` -> Rejects malformed or incorrect credentials aggressively.
    - Line 3: `u = User.query.filter_by(email=d.get('email')).first() or User(email=d.get('email'), github_id="mock_123", github_handle="tester123", github_access_token="mock_t")` -> Asserts the existence of the mock user in the DB.
    - Line 4: `db.session.add(u); db.session.commit()` -> Commits creation.
    - Line 5: `return jsonify(access_token=create_access_token(identity=u.email))` -> Responds with JSON representation of the JWT.

    Returns:
        flask.Response: JSON document specifying the `access_token`.
    """
    d = request.json or {}
    if d.get('email') != 'test@example.com' or d.get('password') != 'test': return jsonify({"msg": "Bad username or password"}), 401
    u = User.query.filter_by(email=d.get('email')).first() or User(email=d.get('email'), github_id="mock_123", github_handle="tester123", github_access_token="mock_t")
    db.session.add(u)
    db.session.commit()
    return jsonify(access_token=create_access_token(identity=u.email))

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Echoes back the currently authenticated user's identity.

    ### How to Use
    Send a GET request here containing the raw JWT Bearer token in headers.

    ### Why this function was used
    Acts as a heartbeat component for the frontend to verify that its current token remains valid.

    ### How to change in the future
    Consider expanding this to return user profile data instead of just the email string.

    ### Detailed Line-by-Line Execution
    - Line 1: `return jsonify(logged_in_as=get_jwt_identity()), 200` -> Fetches the identity parsed from the verified JWT and serializes it out.

    Returns:
        flask.Response: JSON tracking the identity string.
    """
    return jsonify(logged_in_as=get_jwt_identity()), 200

@auth_bp.route('/sandbox', methods=['GET', 'POST'])
@jwt_required()
def sandbox():
    """
    Aggregated route to either load or update user sandbox code.

    ### How to Use
    GET to retrieve current sandbox code. POST `{code: "..."}` to save code.

    ### Why this function was used
    Minimizes code footprint by handling both reads and updates of a user's sandbox property in one route block.

    ### How to change in the future
    If expanding to multiple files conceptually, break this out to an independent `SandboxController`.

    ### Detailed Line-by-Line Execution
    - Line 1: `u = User.query.filter_by(email=get_jwt_identity()).first()` -> Identifies user context natively from JWT.
    - Line 2: `if not u: return jsonify({"error": "User not found"}), 404` -> Safely bails if token doesn't match an active database record.
    - Line 3: `if request.method == 'POST': u.sandbox_code = request.json.get('code', ''); db.session.commit(); return jsonify({"message": "Sandbox code saved"})` -> Handles POSTs by mutating the DB property quickly.
    - Line 4: `return jsonify({"code": u.sandbox_code or ""}), 200` -> Resolves the GET operations gracefully.

    Returns:
        flask.Response: Contextual JSON payload containing codes or success messaging.
    """
    u = User.query.filter_by(email=get_jwt_identity()).first()
    if not u: return jsonify({"error": "User not found"}), 404
    if request.method == 'POST':
        u.sandbox_code = request.json.get('code', '')
        db.session.commit()
        return jsonify({"message": "Sandbox code saved"})
    return jsonify({"code": u.sandbox_code or ""}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Terminates standard session tracking (client side enforced placeholder).

    ### How to Use
    Client issues a POST and purges their local token on success.

    ### Why this function was used
    Provides a symantic mechanism to indicate intent of session ending.

    ### How to change in the future
    If strict remote revocation is needed, implement a database blacklist of JWT identifiers.

    ### Detailed Line-by-Line Execution
    - Line 1: `return jsonify({"msg": "Successfully logged out"}), 200` -> Immediately responds with positive assertion.

    Returns:
        flask.Response: JSON notification of exit.
    """
    return jsonify({"msg": "Successfully logged out"}), 200
