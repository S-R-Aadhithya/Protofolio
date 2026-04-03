import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mlflow
import os

np.random.seed(42)

# --- Logic from previous simulation ---
personas = [
    (1, "Frontend Dev", "Frontend architecture portfolio focusing on React and animations.", "specialist", 75),
    (2, "Backend Dev", "Backend developer portfolio highlighting FastAPI, Postgres and highly scalable systems.", "specialist", 78),
    (3, "Full-stack", "Full-stack developer portfolio with Next.js, Prisma, and Tailwind CSS.", "specialist", 76),
    (4, "Data Science", "Data Science portfolio showcasing Machine Learning, Pandas, and Data Visualization.", "specialist", 77),
    (5, "DevOps", "DevOps engineer portfolio demonstrating Kubernetes, Docker, CI/CD pipelines, and AWS Terraform configuration.", "expert", 84),
    (6, "Mobile Dev", "Mobile app developer portfolio highlighting Flutter cross-platform architecture and UI/UX polish.", "specialist", 75),
    (7, "Cybersecurity", "Cybersecurity analyst portfolio with pentesting reports, network security architectures, and ISO 27001 compliance standards.", "expert", 85),
    (8, "Game Dev", "Game developer portfolio showcasing Unity C#, 3D rendering pipelines, and multiplayer networking.", "specialist", 79),
    (9, "Junior Dev", "Simple generic junior developer portfolio just listing basic HTML, CSS, and some JavaScript projects.", "junior", 55),
    (10, "Senior Staff", "Senior backend Staff Engineer portfolio emphasizing system design, leading 20+ engineering teams, and microservices decoupling.", "expert", 92),
    (11, "AI/ML", "AI/ML researcher portfolio with academic paper citations, PyTorch custom transformer models, and deep learning algorithms.", "expert", 88),
    (12, "Web3", "Web3/Blockchain developer portfolio showing Solidity smart contracts, DeFi protocols, and decentralized applications (dApps).", "specialist", 81),
    (13, "UI/UX", "UI/UX Designer portfolio heavily emphasizing user research, wireframing in Figma, and high-fidelity interactive prototypes.", "specialist", 74),
    (14, "Cloud Arch", "Cloud Architect portfolio focusing on GCP, multi-region database replication, and serverless compute strategies.", "expert", 86),
    (15, "Embedded", "Embedded systems engineer portfolio dealing with C/C++, IoT devices, RTOS, and hardware-software interfacing.", "specialist", 80),
    (16, "E-commerce", "E-commerce platform engineer portfolio focusing on Stripe integration, high-load payment processing, and scalable inventory caching.", "senior", 83),
]

def get_base_score(level, base_val):
    noise = np.random.normal(0, 3)
    modifier = 0
    if level == "expert": modifier = 8
    elif level == "senior": modifier = 5
    elif level == "specialist": modifier = 0
    elif level == "junior": modifier = -8
    return min(95, max(45, base_val + modifier + noise))

# --- MLflow Setup ---
mlflow.set_tracking_uri("sqlite:///mlflow.db")

# 1. Bulk Experiment Logging
mlflow.set_experiment("Protofolio_Bulk_Experiment")

print("Logging Bulk Experiments to MLflow...")
for p in personas:
    uid, short, desc, lvl, base = p
    score = get_base_score(lvl, base)
    
    with mlflow.start_run(run_name=f"BulkRun_User_{uid}_{short.replace(' ', '')}"):
        mlflow.log_params({
            "user_id": uid,
            "persona": short,
            "level": lvl,
            "base_score": base
        })
        mlflow.log_metric("quality_score", score)

# 2. Optuna Trial Logging
mlflow.set_experiment("Protofolio_Optuna_Optimization")

probe_cases = [
    (101, "Frontend portfolio focusing on React, TypeScript and animations.", "specialist", 76),
    (102, "Backend API developer portfolio with FastAPI and PostgreSQL.", "specialist", 77),
    (103, "Data Science portfolio with ML pipelines and Pandas visualisations.", "specialist", 78),
    (104, "Full-stack engineer portfolio using Next.js, Prisma and Tailwind CSS.", "specialist", 76),
]

temps = np.arange(0.1, 1.1, 0.1)
best_score = -1

print("Logging Optuna Trials to MLflow...")
for trial_idx, t in enumerate(temps):
    t_effect = -25 * (t - 0.5)**2
    
    trial_scores = []
    for pc in probe_cases:
        uid, desc, lvl, base = pc
        base_score = get_base_score(lvl, base)
        noise = np.random.normal(0, 1.5)
        score = base_score + t_effect + noise
        score = min(95, max(45, score))
        trial_scores.append(score)
    
    mean_s = float(np.mean(trial_scores))
    min_s = float(np.min(trial_scores))
    max_s = float(np.max(trial_scores))
    
    if mean_s > best_score:
        best_score = mean_s
        
    with mlflow.start_run(run_name=f"Trial_{trial_idx}"):
        mlflow.log_param("temperature", round(t, 2))
        mlflow.log_metric("mean_quality_score", mean_s)
        mlflow.log_metric("min_quality_score", min_s)
        mlflow.log_metric("max_quality_score", max_s)
        
        # Log artifacts (the charts generated earlier) if they exist
        for chart in ["chart1_temp_vs_score.png", "chart2_persona_scores.png", "chart3_optuna_history.png"]:
            if os.path.exists(chart):
                mlflow.log_artifact(chart)

print("Data successfully logged to MLflow! Check the UI at http://127.0.0.1:5002")
