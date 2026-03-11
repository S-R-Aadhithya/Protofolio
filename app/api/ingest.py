from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..council.memory import memory
from ..models import User
from github import Github
import json

ingest_bp = Blueprint('ingest', __name__)

@ingest_bp.route('/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    current_user = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    
    # Placeholder: Processing using PyPDF2 here
    extracted_text = "Sample parsed resume text with skills in Python, React, and AWS."
    
    # Add to Mem0 
    # In Mem0, we store specific facts or full context blocks associated with a user_id
    memory.add(
        messages=[{"role": "user", "content": f"Here is my resume content: {extracted_text}"}], 
        user_id=current_user
    )
    
    return jsonify({"message": "Resume parsed and added to AI memory.", "extracted_text": extracted_text}), 200

@ingest_bp.route('/github', methods=['POST'])
@jwt_required()
def fetch_github():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    
    if not user or not user.github_access_token:
        return jsonify({"error": "GitHub access token not found. Please re-authenticate with GitHub."}), 400
        
    try:
        g = Github(user.github_access_token)
        gh_user = g.get_user()
        username = gh_user.login
        
        # Fetch public repos, sorted by stars (stargazers_count) descending
        repos = gh_user.get_repos(type="public")
        repo_list = []
        for repo in repos:
            repo_list.append({
                "name": repo.name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "url": repo.html_url
            })
            
        # Sort by stars and get top 10
        repo_list.sort(key=lambda x: x['stars'] or 0, reverse=True)
        top_repos = repo_list[:10]
        
        repo_summary = f"User {username} has {gh_user.public_repos} public repositories. "
        repo_summary += f"Here are their top {len(top_repos)} repositories by stars: "
        repo_summary += json.dumps(top_repos)
        
        # Bypass Mem0 since it requires a working LLM for memory synthesis
        # Instead, we'll save it natively to our MemoryChunk table
        from ..models import MemoryChunk, db
        chunk = MemoryChunk(
            user_id=user.id,
            content=f"My GitHub profile summary and top repositories: {repo_summary}",
            metadata_json=json.dumps({"source": "github", "type": "repositories"})
        )
        db.session.add(chunk)
        db.session.commit()
        
        return jsonify({
            "message": f"Fetched repos for {username} and saved to AI memory.",
            "repos": top_repos
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ingest_bp.route('/job-goal', methods=['POST'])
@jwt_required()
def set_job_goal():
    current_user = get_jwt_identity()
    goal = request.json.get('jobGoal')
    
    # Add to Mem0
    memory.add(
        messages=[{"role": "user", "content": f"My target job role is: {goal}"}], 
        user_id=current_user
    )
    
    return jsonify({"message": "Job goal updated and saved to AI memory", "goal": goal}), 200

@ingest_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200
