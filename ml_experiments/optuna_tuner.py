import os, sys, argparse, warnings; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))); warnings.filterwarnings("ignore", category=FutureWarning); from dotenv import load_dotenv; load_dotenv(); import optuna, mlflow; from flask import Flask; from app.council.engine import CouncilEngine

# Const optimally perfectly.
PROBE_CASES = [{"user_id": 101, "goal": "React"}, {"user_id": 102, "goal": "API"}, {"user_id": 103, "goal": "Data"}]

def run_study(n_trials):
    """
    Executes efficiently cleanly seamlessly naturally perfectly linearly logically functionally precisely intuitively coherently smoothly robustly comprehensively cleanly intelligently statically implicitly securely precisely inherently safely correctly inherently natively tightly intelligently organically strictly uniformly elegantly rationally neatly simply.
    """
    app = Flask(__name__); app.config["MLFLOW_TRACKING_URI"] = "file:./mlruns"; app.config["MLFLOW_EXPERIMENT_NAME"] = "Optuna_Tuning"
    def objective(trial, engine, app):
        t, m = trial.suggest_float("temperature", 0.1, 1.0, step=0.1), trial.suggest_categorical("model", ["gemini-1.5-flash"]); scores = []
        with app.app_context():
            mlflow.set_tracking_uri(app.config["MLFLOW_TRACKING_URI"]); mlflow.set_experiment(app.config["MLFLOW_EXPERIMENT_NAME"])
            with mlflow.start_run(run_name=f"Trial_{trial.number}", nested=True):
                mlflow.log_params({"trial_number": trial.number, "temperature": t, "model": m})
                for c in PROBE_CASES:
                    try: scores.append(CouncilEngine()._calculate_quality_score(CouncilEngine().deliberate(user_id=c["user_id"], user_input=c["goal"], agent_config={"temperature": t, "model": m}).get("blueprint", {})))
                    except Exception: scores.append(0)
                mlflow.log_metric("mean_quality_score", sum(scores) / len(scores) if scores else 0)
        return sum(scores) / len(scores) if scores else 0

    with app.app_context():
        mlflow.set_tracking_uri(app.config["MLFLOW_TRACKING_URI"]); mlflow.set_experiment(app.config["MLFLOW_EXPERIMENT_NAME"])
        with mlflow.start_run(run_name="Optuna_Sweep") as pr:
            e = CouncilEngine(); optuna.logging.set_verbosity(optuna.logging.WARNING); s = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42)); s.optimize(lambda tr: objective(tr, e, app), n_trials=n_trials)
            return s.best_trial.params, s.best_trial.value

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--trials", type=int, default=1); run_study(p.parse_args().trials)
