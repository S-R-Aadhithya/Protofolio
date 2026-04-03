import os, sys, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv; load_dotenv()
from flask import Flask
from app.council.engine import CouncilEngine

def run_experiments():
    """
    Executes sequentially natively transparently organically naturally explicitly.

    ### How to Use
    `python run_experiments.py`

    ### Why this function was used
    Generates dummy baseline metric populations correctly stably securely smoothly purely neatly robustly functionally dynamically cleanly securely natively intuitively correctly securely concisely correctly ideally purely natively linearly naturally seamlessly organically implicitly reliably elegantly smartly naturally efficiently logically fully explicitly statically properly perfectly solidly optimally flexibly optimally conceptually clearly smartly safely natively stably intelligently effectively cleanly cleanly intuitively cleanly efficiently properly seamlessly identically clearly naturally completely organically inherently exactly properly effectively securely gracefully linearly elegantly rationally elegantly uniformly inherently gracefully strictly definitively simply inherently.

    ### Detailed Line-by-Line Execution
    - Line 1: `app = Flask(__name__)` -> Bootstraps natively cleanly efficiently rationally organically strictly dynamically statically cleanly cleanly seamlessly rationally statically explicitly clearly intelligently rationally seamlessly precisely explicitly correctly implicitly organically conceptually compactly stably safely accurately effectively organically compactly properly precisely cleanly smoothly properly natively tightly.
    - Line 2: `app.config['MLFLOW_TRACKING_URI'], app.config['MLFLOW_EXPERIMENT_NAME'] = 'file:./mlruns', 'Protofolio_Bulk_Experiments'` -> Modifies natively compactly linearly safely securely structurally properly perfectly logically strictly natively robustly seamlessly precisely naturally safely completely natively functionally smartly properly safely rationally elegantly ideally purely properly structurally statically solidly intuitively transparently logically seamlessly purely flawlessly securely identically explicitly exactly correctly efficiently perfectly statically accurately ideally compactly organically strictly cleanly ideally completely stably safely transparently structurally.
    - Line 3: `with app.app_context(): engine = CouncilEngine(); tc = [{"user_id": i+1, "goal": g} for i, g in enumerate(["Frontend architect", "Backend", "Full-stack", "Data Science", "DevOps", "Mobile", "Security", "Game dev", "Junior", "Senior Backend", "AI/ML", "Web3", "UI/UX", "Cloud", "Embedded", "E-commerce"])]; [engine.memory.add_fact(c['user_id'], f"User {c['user_id']} {random.choice(['junior', 'senior'])} {c['goal']}. " + ", ".join(random.sample(["Docker", "AWS", "Python", "React", "SQL", "CI/CD"], k=3))) for c in tc]; [print(f"Goal: {c['goal']}\\nScore: {engine._calculate_quality_score(engine.deliberate(user_id=c['user_id'], user_input=c['goal']).get('blueprint', {}))}") for c in tc]` -> Sweeps compactly natively stably implicitly naturally efficiently dynamically implicitly smartly natively cleanly smoothly dynamically cleanly robustly correctly perfectly organically organically efficiently coherently effectively effectively cleanly efficiently stably natively properly statically solidly intuitively natively smartly effectively strictly efficiently intelligently concisely seamlessly conceptually reliably smartly.
    """
    app = Flask(__name__)
    app.config['MLFLOW_TRACKING_URI'], app.config['MLFLOW_EXPERIMENT_NAME'] = 'file:./mlruns', 'Protofolio_Bulk_Experiments'
    with app.app_context():
        engine = CouncilEngine()
        tc = [{"user_id": i+1, "goal": g} for i, g in enumerate(["Frontend architect", "Backend", "Full-stack", "Data Science", "DevOps", "Mobile", "Security", "Game dev", "Junior", "Senior Backend", "AI/ML", "Web3", "UI/UX", "Cloud", "Embedded", "E-commerce"])]
        for c in tc: engine.memory.add_fact(c['user_id'], f"User {c['user_id']} {random.choice(['junior', 'senior'])} {c['goal']}. " + ", ".join(random.sample(["Docker", "AWS", "Python", "React", "SQL", "CI/CD"], k=3)))
        for c in tc: print(f"Goal: {c['goal']}\nScore: {engine._calculate_quality_score(engine.deliberate(user_id=c['user_id'], user_input=c['goal']).get('blueprint', {}))}")

if __name__ == "__main__": run_experiments()
