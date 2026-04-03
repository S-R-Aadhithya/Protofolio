"""
optuna_tuner.py
===============
Optuna hyperparameter search for the Protofolio LLM Council.

Optimises `temperature` (and optionally `model`) to maximise
the `quality_score` metric produced by the council deliberation.

Each Optuna trial is logged as a nested MLflow child run under the
parent experiment "Optuna_Tuning". Best parameters are printed and
tagged on the parent run.

Usage:
    python optuna_tuner.py [--trials N]
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import argparse
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from dotenv import load_dotenv
load_dotenv()

import optuna
import mlflow

from flask import Flask
from app.council.engine import CouncilEngine

# ------------------------------------------------------------------
# Optuna search space
# ------------------------------------------------------------------
# We deliberately keep the search space small so the study completes
# in CI without real API calls (fallback mock mode is fine — the
# quality_score still varies with the blueprint randomness seeded
# by temperature).
TEMPERATURE_LOW  = 0.1
TEMPERATURE_HIGH = 1.0
MODEL_CHOICES    = ["gemini-1.5-flash"]   # add "gemini-1.5-pro" when billing is enabled
N_TRIALS_DEFAULT = 10

# Representative goals – a small cross-section covers frontend,
# backend, data-science and edge cases.
PROBE_CASES = [
    {"user_id": 101, "goal": "Frontend portfolio focusing on React, TypeScript and animations."},
    {"user_id": 102, "goal": "Backend API developer portfolio with FastAPI and PostgreSQL."},
    {"user_id": 103, "goal": "Data Science portfolio with ML pipelines and Pandas visualisations."},
    {"user_id": 104, "goal": "Full-stack engineer portfolio using Next.js, Prisma and Tailwind CSS."},
]


def build_app():
    """Create a minimal Flask app context for engine initialisation."""
    app = Flask(__name__)
    app.config["MLFLOW_TRACKING_URI"]    = "file:./mlruns"
    app.config["MLFLOW_EXPERIMENT_NAME"] = "Optuna_Tuning"
    return app


def objective(trial, engine, app):
    """
    Optuna objective function.

    Samples hyperparameters, runs all probe cases with those params,
    and returns the mean quality_score (higher is better).
    """
    # ── Suggest hyperparameters ────────────────────────────────────
    temperature = trial.suggest_float("temperature", TEMPERATURE_LOW, TEMPERATURE_HIGH, step=0.1)
    model       = trial.suggest_categorical("model", MODEL_CHOICES)

    agent_config = {"temperature": temperature, "model": model}

    scores = []

    with app.app_context():
        mlflow.set_tracking_uri(app.config["MLFLOW_TRACKING_URI"])
        mlflow.set_experiment(app.config["MLFLOW_EXPERIMENT_NAME"])

        # Each trial is a child run nested under the parent sweep run
        with mlflow.start_run(run_name=f"Trial_{trial.number}", nested=True):
            mlflow.log_params({
                "trial_number": trial.number,
                "temperature":  temperature,
                "model":        model,
            })

            for case in PROBE_CASES:
                try:
                    # Re-initialise engine agents with current trial config
                    engine = CouncilEngine()
                    result    = engine.deliberate(
                        user_id=case["user_id"],
                        user_input=case["goal"],
                        agent_config=agent_config,
                    )
                    blueprint = result.get("blueprint", {})
                    score     = engine._calculate_quality_score(blueprint)
                    scores.append(score)
                    print(f"  Trial {trial.number} | T={temperature:.1f} | {case['goal'][:35]}... -> score {score}")
                except Exception as exc:
                    print(f"  Trial {trial.number} WARNING: {exc}")
                    scores.append(0)

            mean_score = sum(scores) / len(scores) if scores else 0
            mlflow.log_metric("mean_quality_score", mean_score)
            mlflow.log_metric("min_quality_score",  min(scores) if scores else 0)
            mlflow.log_metric("max_quality_score",  max(scores) if scores else 0)

    return mean_score


def run_study(n_trials: int):
    app = build_app()

    with app.app_context():
        mlflow.set_tracking_uri(app.config["MLFLOW_TRACKING_URI"])
        mlflow.set_experiment(app.config["MLFLOW_EXPERIMENT_NAME"])

        # Parent MLflow run wraps the entire Optuna study
        with mlflow.start_run(run_name="Optuna_Sweep") as parent_run:
            mlflow.log_params({
                "n_trials":        n_trials,
                "temperature_low": TEMPERATURE_LOW,
                "temperature_high":TEMPERATURE_HIGH,
                "models_searched": str(MODEL_CHOICES),
                "probe_cases":     len(PROBE_CASES),
            })

            engine = CouncilEngine()

            # Suppress Optuna's verbose trial logs; keep our own prints
            optuna.logging.set_verbosity(optuna.logging.WARNING)

            study = optuna.create_study(
                study_name="council_temperature_sweep",
                direction="maximize",
                sampler=optuna.samplers.TPESampler(seed=42),
            )

            study.optimize(
                lambda trial: objective(trial, engine, app),
                n_trials=n_trials,
                show_progress_bar=False,
            )

            # ── Log best results to parent run ────────────────────
            best = study.best_trial
            mlflow.log_params({
                "best_temperature": best.params["temperature"],
                "best_model":       best.params["model"],
            })
            mlflow.log_metric("best_mean_quality_score", best.value)
            mlflow.set_tag("optuna_study_name", study.study_name)
            mlflow.set_tag("parent_run_id", parent_run.info.run_id)

            print("\n" + "="*60)
            print(f"Optuna study complete — {n_trials} trials")
            print(f"  Best temperature      : {best.params['temperature']:.1f}")
            print(f"  Best model            : {best.params['model']}")
            print(f"  Best mean quality score: {best.value:.1f}")
            print("="*60)

            return best.params, best.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optuna tuner for Protofolio LLM Council")
    parser.add_argument("--trials", type=int, default=N_TRIALS_DEFAULT,
                        help=f"Number of Optuna trials (default: {N_TRIALS_DEFAULT})")
    args = parser.parse_args()
    run_study(args.trials)
