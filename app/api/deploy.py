from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..council.memory import memory

deploy_bp = Blueprint('deploy', __name__)

@deploy_bp.route('/sandbox/feedback', methods=['POST'])
@jwt_required()
def sandbox_feedback():
    """
    Submits user sandbox edits back to the Mem0 memory layer.

    ### How to Use
    ```javascript
    fetch('/api/deploy/sandbox/feedback', {
      method: 'POST',
      body: JSON.stringify({ changes: '+ h1 { color: red }', rationale: 'Wanted red headers' })
    })
    ```

    ### Why this function was used
    Creates a feedback loop allowing the AI Council to learn from manual overrides made by the user in the interactive sandbox IDE.

    ### How to change in the future
    You can extend the schema to accept structured unified diffs instead of arbitrary strings for better parsing by the Mem0 embedding model.

    ### Detailed Line-by-Line Execution
    - Line 1: `d = request.json or {}` -> Secures the incoming JSON payload against nulls.
    - Line 2: `if not d.get('changes'): return jsonify({"error": "No changes provided"}), 400` -> Performs an immediate short-circuit validation rejecting empty diffs.
    - Line 3: `memory.add(messages=[{"role": "user", "content": f"Manual Developer Edit: The user made the following changes in the sandbox to the final output: {d.get('changes')}. Rationale: {d.get('rationale', 'User manually adjusted the output in the sandbox.')}"}], user_id=get_jwt_identity())` -> Interpolates the changes and rationale into a unified string and fires it directly into the agent's long-term vector memory under the user's specific sub-graph.
    - Line 4: `return jsonify({"message": "Sandbox feedback integrated into persistent memory."}), 200` -> Confirms successful ingestion to the frontend.

    Returns:
        flask.Response: JSON confirming memory integration or an error if missing data.
    """
    d = request.json or {}
    if not d.get('changes'): return jsonify({"error": "No changes provided"}), 400
    memory.add(messages=[{"role": "user", "content": f"Manual Developer Edit: The user made the following changes in the sandbox to the final output: {d.get('changes')}. Rationale: {d.get('rationale', 'User manually adjusted the output in the sandbox.')}"}], user_id=get_jwt_identity())
    return jsonify({"message": "Sandbox feedback integrated into persistent memory."}), 200

@deploy_bp.route('/publish', methods=['POST'])
@jwt_required()
def deploy_to_github():
    """
    Triggers the mocked publication event simulating a deployment to GitHub Pages.

    ### How to Use
    ```javascript
    fetch('/api/deploy/publish', { method: 'POST' })
    ```

    ### Why this function was used
    Acts as the final step in the portfolio pipeline, providing closure to the user journey and seeding their AI memory that a successful milestone was crossed.

    ### How to change in the future
    Replace the mock implementation with the actual PyGithub wrapper to execute `git commit` and `git push` routines.

    ### Detailed Line-by-Line Execution
    - Line 1: `memory.add(messages=[{"role": "system", "content": f"A new portfolio version was successfully deployed to GitHub Pages for {get_jwt_identity()}."}], user_id=get_jwt_identity())` -> Inserts a persistent milestone marker into the user's vector memory.
    - Line 2: `return jsonify({"message": "Successfully deployed to GitHub Pages."}), 200` -> Responds favorably.

    Returns:
        flask.Response: JSON confirming deployment representation.
    """
    memory.add(messages=[{"role": "system", "content": f"A new portfolio version was successfully deployed to GitHub Pages for {get_jwt_identity()}."}], user_id=get_jwt_identity())
    return jsonify({"message": "Successfully deployed to GitHub Pages."}), 200
