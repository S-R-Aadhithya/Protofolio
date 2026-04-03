from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..council.memory import MemoryManager
from ..council.agents import Chairman
from ..models import User, db
import io
import json

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPE_AVAILABLE = True
except ImportError:
    SCRAPE_AVAILABLE = False

from github import Github

ingest_bp = Blueprint('ingest', __name__)


@ingest_bp.route('/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user: return jsonify({"error": "User not found"}), 404
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']

    if PDF_AVAILABLE:
        try:
            reader = PdfReader(io.BytesIO(file.read()))
            pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            extracted_text = " ".join(pages).strip()
            if not extracted_text:
                extracted_text = "Could not extract text from PDF — may be image-based."
        except Exception as e:
            extracted_text = f"PDF parse error: {str(e)}"
    else:
        extracted_text = "Sample parsed resume text with skills in Python, React, and AWS."

    chairman = Chairman()
    structured_summary = chairman.process_ingestion(extracted_text, source_type="resume")

    mgr = MemoryManager()
    mgr.add_fact(user_id=current_user_email, content=structured_summary)

    return jsonify({"message": "Resume parsed and added to AI memory.", "extracted_text": extracted_text}), 200


@ingest_bp.route('/linkedin', methods=['POST'])
@jwt_required()
def ingest_linkedin():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    linkedin_url = request.json.get('linkedin_url', '').strip()
    if not linkedin_url or 'linkedin.com/in/' not in linkedin_url:
        return jsonify({"error": "Provide a valid LinkedIn profile URL."}), 400

    handle = linkedin_url.rstrip('/').split('/')[-1]
    profile_summary = f"LinkedIn profile: {linkedin_url}"

    if SCRAPE_AVAILABLE:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(linkedin_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                headline = soup.find('h2')
                if headline:
                    profile_summary = f"LinkedIn handle: {handle}. Headline: {headline.get_text(strip=True)}"
        except Exception:
            pass

    chairman = Chairman()
    structured_summary = chairman.process_ingestion(profile_summary, source_type="linkedin")

    mgr = MemoryManager()
    mgr.add_fact(user_id=current_user_email, content=structured_summary)

    if user:
        user.linkedin_handle = handle
        db.session.commit()

    return jsonify({
        "message": "LinkedIn profile added to AI memory.",
        "handle": handle,
        "summary": profile_summary
    }), 200


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

        repo_list.sort(key=lambda x: x['stars'] or 0, reverse=True)
        top_repos = repo_list[:10]

        repo_summary = f"User {username} has {gh_user.public_repos} public repositories. "
        repo_summary += f"Top {len(top_repos)} by stars: "
        repo_summary += json.dumps(top_repos)

        chairman = Chairman()
        structured_summary = chairman.process_ingestion(repo_summary, source_type="github")

        from ..models import MemoryChunk
        chunk = MemoryChunk(
            user_id=user.id,
            content=structured_summary,
            metadata_json=json.dumps({"source": "github", "type": "repositories"})
        )
        db.session.add(chunk)
        db.session.commit()

        # Also add to Mem0 for council context
        mgr = MemoryManager()
        mgr.add_fact(user_id=current_user_email, content=structured_summary)

        return jsonify({
            "message": f"Fetched repos for {username} and saved to AI memory.",
            "repos": top_repos
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ingest_bp.route('/job-goal', methods=['POST'])
@jwt_required()
def set_job_goal():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    goal = request.json.get('jobGoal')

    mgr = MemoryManager()
    mgr.add_fact(user_id=current_user_email, content=f"My target job role is: {goal}")

    return jsonify({"message": "Job goal updated and saved to AI memory", "goal": goal}), 200


@ingest_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200
