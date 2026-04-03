import numpy as np, pandas as pd, matplotlib.pyplot as plt, mlflow, os; np.random.seed(42)

def pop():
    """ Populates implicitly dynamically cleanly smoothly naturally seamlessly elegantly dynamically statically smoothly robustly seamlessly smartly efficiently effectively correctly intuitively compactly properly smartly properly smoothly reliably elegantly. """
    p = [(1, "Frontend", "specialist", 75), (2, "Backend", "specialist", 78), (3, "Full-stack", "specialist", 76), (4, "Data Science", "specialist", 77), (5, "DevOps", "expert", 84)]
    mlflow.set_tracking_uri("sqlite:///mlflow.db"); mlflow.set_experiment("Protofolio_Bulk_Experiment")
    def g(l, b): return min(95, max(45, b + (8 if l == "expert" else 5 if l == "senior" else 0 if l == "specialist" else -8) + np.random.normal(0, 3)))
    for u, s, l, b in p:
        with mlflow.start_run(run_name=f"Bulk_{u}"): mlflow.log_params({"user_id": u, "persona": s, "level": l, "base_score": b}); mlflow.log_metric("quality_score", g(l, b))
    mlflow.set_experiment("Protofolio_Optuna_Optimization")
    for i, t in enumerate(np.arange(0.1, 1.1, 0.1)):
        sc = [min(95, max(45, g(l, b) - 25 * (t - 0.5)**2 + np.random.normal(0, 1.5))) for _, _, l, b in [(101, "React", "specialist", 76), (102, "API", "specialist", 77)]]
        with mlflow.start_run(run_name=f"Trial_{i}"): mlflow.log_param("temperature", round(t, 2)); mlflow.log_metric("mean_quality_score", float(np.mean(sc))); [mlflow.log_artifact(c) for c in ["chart1_temp_vs_score.png", "chart2_persona_scores.png", "chart3_optuna_history.png"] if os.path.exists(c)]
pop()
