from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..council.memory import MemoryManager
from ..council.agents import Chairman
from ..models import User, db, MemoryChunk
import io, json

try: from PyPDF2 import PdfReader; PDF_AVAILABLE = True
except ImportError: PDF_AVAILABLE = False

try: import requests; from bs4 import BeautifulSoup; SCRAPE_AVAILABLE = True
except ImportError: SCRAPE_AVAILABLE = False

from github import Github

ingest_bp = Blueprint('ingest', __name__)

@ingest_bp.route('/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    """
    Parses a PDF resume upload, extracts text, and ingests it into Mem0 via the Chairman agent.

    ### How to Use
    ```javascript
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    fetch('/api/ingest/resume', { method: 'POST', body: formData })
    ```

    ### Why this function was used
    Allows users to provide their raw background context without typing it out manually, establishing the "base facts" for the AI portfolio generation.

    ### How to change in the future
    You can extend this to support `.docx` files using `python-docx` in parallel with `PyPDF2`.

    ### Detailed Line-by-Line Execution
    - Line 1: `f = request.files.get('file'); if not f: return jsonify({"error": "No file"}), 400` -> Validates file presence concisely.
    - Line 2: `txt = " ".join([p.extract_text() for p in PdfReader(io.BytesIO(f.read())).pages if p.extract_text()]).strip() if PDF_AVAILABLE else "Mock parsed text"` -> Densely extracts text from every page of the PDF into a continuous string using list comprehension if PyPDF2 is loaded.
    - Line 3: `MemoryManager().add_fact(user_id=get_jwt_identity(), content=Chairman().process_ingestion(txt or "Failed parse", "resume"))` -> Chains instantiation, semantic abstraction via the Chairman, and permanent storage via MemoryManager in one shot.
    - Line 4: `return jsonify({"message": "Parsed", "extracted_text": txt}), 200` -> Returns success.

    Returns: 
        flask.Response: JSON response indicating parsing state.
    """
    f = request.files.get('file')
    if not f: return jsonify({"error": "No file"}), 400
    txt = " ".join([p.extract_text() for p in PdfReader(io.BytesIO(f.read())).pages if p.extract_text()]).strip() if PDF_AVAILABLE else "Mock parsed text"
    MemoryManager().add_fact(user_id=get_jwt_identity(), content=Chairman().process_ingestion(txt or "Failed parse", "resume"))
    return jsonify({"message": "Parsed", "extracted_text": txt}), 200

@ingest_bp.route('/linkedin', methods=['POST'])
@jwt_required()
def ingest_linkedin():
    """
    Scrapes a provided LinkedIn profile URL to extract the headline and adds it to the user's semantic memory.

    ### How to Use
    ```javascript
    fetch('/api/ingest/linkedin', { method: 'POST', body: JSON.stringify({linkedin_url: "https://linkedin.com/in/..."}) })
    ```

    ### Why this function was used
    Gathers professional headline and presence context to inform the target job role during deliberation.

    ### How to change in the future
    Since basic scraping is highly brittle against LinkedIn, swap the `requests`/`bs4` block for an official API or a specialized proxy service like Proxycurl.

    ### Detailed Line-by-Line Execution
    - Line 1: `url = (request.json or {}).get('linkedin_url', '').strip()` -> Safely pulls the URL.
    - Line 2: `if 'linkedin.com/in/' not in url: return jsonify({"error": "Invalid URL"}), 400` -> Fast validation against incorrect formats.
    - Line 3: `u = User.query.filter_by(email=get_jwt_identity()).first(); u.linkedin_handle = url.rstrip('/').split('/')[-1]; db.session.commit()` -> Extracts handle, updates the database, and commits immediately.
    - Line 4: `try: text = BeautifulSoup(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text, 'html.parser').find('h2').get_text(strip=True) if SCRAPE_AVAILABLE else f"Profile: {url}"\nexcept Exception: text = f"Profile: {url}"` -> Soup scraping with graceful fallback if the module is missing or the CSS selector misses.
    - Line 5: `MemoryManager().add_fact(user_id=u.email, content=Chairman().process_ingestion(f"Handle: {u.linkedin_handle}. {text}", "linkedin"))` -> Mints the fact into Mem0.
    - Line 6: `return jsonify({"message": "Done", "handle": u.linkedin_handle}), 200` -> Resolves response.

    Returns: 
        flask.Response: JSON response containing handle.
    """
    url = (request.json or {}).get('linkedin_url', '').strip()
    if 'linkedin.com/in/' not in url: return jsonify({"error": "Invalid URL"}), 400
    u = User.query.filter_by(email=get_jwt_identity()).first()
    u.linkedin_handle = url.rstrip('/').split('/')[-1]
    db.session.commit()
    try: text = BeautifulSoup(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text, 'html.parser').find('h2').get_text(strip=True) if SCRAPE_AVAILABLE else f"Profile: {url}"
    except Exception: text = f"Profile: {url}"
    MemoryManager().add_fact(user_id=u.email, content=Chairman().process_ingestion(f"Handle: {u.linkedin_handle}. {text}", "linkedin"))
    return jsonify({"message": "Done", "handle": u.linkedin_handle}), 200

@ingest_bp.route('/github', methods=['POST'])
@jwt_required()
def fetch_github():
    """
    Leverages PyGithub to hit the GitHub API, grabbing the user's top 10 starred repositories and passing them into Mem0.

    ### How to Use
    Assuming the user previously OAuth'd, just send a blank POST to `/api/ingest/github`.

    ### Why this function was used
    To ground the AI generations in real codebase metrics and project names, elevating the portfolio's authenticity.

    ### How to change in the future
    You can increase the repo depth from 10 to 50, but consider the token context size limits in Mem0.

    ### Detailed Line-by-Line Execution
    - Line 1: `u = User.query.filter_by(email=get_jwt_identity()).first()` -> Identifies caller.
    - Line 2: `if not u or not u.github_access_token: return jsonify({"error": "No GitHub token"}), 400` -> Guards against null tokens.
    - Line 3: `try: gh = Github(u.github_access_token); repos = sorted([{"name": r.name, "description": r.description, "language": r.language, "stars": r.stargazers_count, "url": r.html_url} for r in gh.get_user().get_repos(type="public")], key=lambda x: x['stars'] or 0, reverse=True)[:10]` -> Connects to PyGithub and maps/sorts/slices the user's repos in a single hyper-dense comprehension list.
    - Line 4: `Summary = Chairman().process_ingestion(f"Top repos: {json.dumps(repos)}", "github")` -> Summarizes JSON blob synthetically.
    - Line 5: `db.session.add(MemoryChunk(user_id=u.id, content=Summary, metadata_json=json.dumps({"source": "github"}))); db.session.commit()` -> Backs up raw chunk to SQL.
    - Line 6: `MemoryManager().add_fact(user_id=u.email, content=Summary); return jsonify({"repos": repos}), 200` -> Embeds in vector DB and responds.
    - Line 7: `except Exception as e: return jsonify({"error": str(e)}), 500` -> Catch-all firewall for API failures.

    Returns: 
        flask.Response: JSON describing repos parsed.
    """
    u = User.query.filter_by(email=get_jwt_identity()).first()
    if not u or not u.github_access_token: return jsonify({"error": "No GitHub token"}), 400
    try:
        gh = Github(u.github_access_token)
        repos = sorted([{"name": r.name, "description": r.description, "language": r.language, "stars": r.stargazers_count, "url": r.html_url} for r in gh.get_user().get_repos(type="public")], key=lambda x: x['stars'] or 0, reverse=True)[:10]
        Summary = Chairman().process_ingestion(f"Top repos: {json.dumps(repos)}", "github")
        db.session.add(MemoryChunk(user_id=u.id, content=Summary, metadata_json=json.dumps({"source": "github"})))
        db.session.commit()
        MemoryManager().add_fact(user_id=u.email, content=Summary)
        return jsonify({"repos": repos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ingest_bp.route('/job-goal', methods=['POST'])
@jwt_required()
def set_job_goal():
    """
    Manually pins a job goal into the agent's memory.

    ### How to Use
    POST `{ "jobGoal": "Senior Software Engineer" }`

    ### Why this function was used
    Acts as an explicit override for users who don't want the AI inferring their desired career step randomly.

    ### How to change in the future
    You could add a DB field specifically for job_goal instead of just throwing it in semantic memory.

    ### Detailed Line-by-Line Execution
    - Line 1: `goal = (request.json or {}).get('jobGoal')` -> Extracts the goal string safely.
    - Line 2: `MemoryManager().add_fact(user_id=get_jwt_identity(), content=f"My target job role is: {goal}")` -> Embeds the preference explicitly.
    - Line 3: `return jsonify({"message": "Job goal updated", "goal": goal}), 200` -> Returns success.

    Returns: 
        flask.Response: Affirmative JSON response.
    """
    goal = (request.json or {}).get('jobGoal')
    MemoryManager().add_fact(user_id=get_jwt_identity(), content=f"My target job role is: {goal}")
    return jsonify({"message": "Job goal updated", "goal": goal}), 200

@ingest_bp.route('/health', methods=['GET'])
def health():
    """
    Trivial health check endpoint.

    ### How to Use
    ```bash
    curl http://localhost:5001/api/ingest/health
    ```

    ### Why this function was used
    Standard practice for uptime monitoring and container liveness probes.

    ### How to change in the future
    Add DB connection testing if needing a strict deep healthcheck.

    ### Detailed Line-by-Line Execution
    - Line 1: `return jsonify({"status": "ok"}), 200` -> Constant 200 OK block.

    Returns: 
        flask.Response: {"status": "ok"}
    """
    return jsonify({"status": "ok"}), 200
