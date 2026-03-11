import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..council.memory import memory

deploy_bp = Blueprint('deploy', __name__)

@deploy_bp.route('/sandbox/feedback', methods=['POST'])
@jwt_required()
def sandbox_feedback():
    """
    When a developer edits the code manually in the Sandbox UI, 
    the frontend sends the feedback/diff here.
    We store it directly into Mem0 so the Architecture and Design council 
    takes it into account during the next generation.
    """
    current_user = get_jwt_identity()
    data = request.json
    
    code_changes = data.get('changes')
    rationale = data.get('rationale', 'User manually adjusted the output in the sandbox.')
    
    if not code_changes:
        return jsonify({"error": "No changes provided"}), 400
        
    feedback_payload = f"Manual Developer Edit: The user made the following changes in the sandbox to the final output: {code_changes}. Rationale: {rationale}"
    
    # Add manual feedback directly into AI Memory
    memory.add(
        messages=[{"role": "user", "content": feedback_payload}], 
        user_id=current_user
    )
    
    return jsonify({"message": "Sandbox feedback integrated into persistent memory."}), 200

@deploy_bp.route('/publish', methods=['POST'])
@jwt_required()
def deploy_to_github():
    """
    Dummy route demonstrating final publication.
    Code is pushed to a new repo via PyGithub using the user's PAT.
    """
    current_user = get_jwt_identity()
    
    # Store the fact that a deployment occurred as historical context
    memory.add(
        messages=[{"role": "system", "content": f"A new portfolio version was successfully deployed to GitHub Pages for {current_user}."}], 
        user_id=current_user
    )
    
    return jsonify({"message": "Successfully deployed to GitHub Pages."}), 200
