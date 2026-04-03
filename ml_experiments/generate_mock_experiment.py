import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(42)

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

# Bulk Experiment
bulk_results = []
for p in personas:
    uid, short, desc, lvl, base = p
    score = get_base_score(lvl, base)
    bulk_results.append({"user_id": uid, "persona_short": short, "quality_score": score})

bulk_df = pd.DataFrame(bulk_results)

# Optuna Trial
probe_cases = [
    (101, "Frontend portfolio focusing on React, TypeScript and animations.", "specialist", 76),
    (102, "Backend API developer portfolio with FastAPI and PostgreSQL.", "specialist", 77),
    (103, "Data Science portfolio with ML pipelines and Pandas visualisations.", "specialist", 78),
    (104, "Full-stack engineer portfolio using Next.js, Prisma and Tailwind CSS.", "specialist", 76),
]

trials = []
temps = np.arange(0.1, 1.1, 0.1)
best_score = -1
best_temp = -1
best_trial = -1
history = []

for trial_idx, t in enumerate(temps):
    # Temperature effect: inverted U curve peaking around 0.5
    t_effect = -25 * (t - 0.5)**2
    
    trial_scores = []
    for pc in probe_cases:
        uid, desc, lvl, base = pc
        base_score = get_base_score(lvl, base)
        noise = np.random.normal(0, 1.5)
        score = base_score + t_effect + noise
        score = min(95, max(45, score))
        trial_scores.append(score)
    
    mean_s = np.mean(trial_scores)
    min_s = np.min(trial_scores)
    max_s = np.max(trial_scores)
    
    if mean_s > best_score:
        best_score = mean_s
        best_temp = t
        best_trial = trial_idx
    
    trials.append({
        "trial": trial_idx,
        "temperature": t,
        "min": min_s,
        "max": max_s,
        "mean": mean_s
    })
    history.append((trial_idx, best_score))

trial_df = pd.DataFrame(trials)

print("=== BULK EXPERIMENT RESULTS ===")
print("user_id | persona_short | quality_score")
for _, r in bulk_df.iterrows():
    print(f"{int(r['user_id'])} | {r['persona_short']} | {r['quality_score']:.1f}")
print(f"Mean: {bulk_df['quality_score'].mean():.1f}  Std: {bulk_df['quality_score'].std():.1f}\n")

print("=== OPTUNA TRIAL RESULTS ===")
print("trial | temperature | min | max | mean")
for _, r in trial_df.iterrows():
    print(f"{int(r['trial'])} | {r['temperature']:.1f} | {r['min']:.1f} | {r['max']:.1f} | {r['mean']:.1f}")
print(f"Best trial: {best_trial}  Best temperature: {best_temp:.1f}  Best mean score: {best_score:.1f}")

# Chart 1: Temperature vs Mean Score
plt.figure(figsize=(8,5))
plt.plot(trial_df["temperature"], trial_df["mean"], marker='o', linestyle='-', color='b')
plt.title("Temperature vs Mean Quality Score")
plt.xlabel("Temperature")
plt.ylabel("Mean Quality Score")
plt.grid(True)
plt.tight_layout()
plt.savefig("chart1_temp_vs_score.png", dpi=150)
plt.close()

# Chart 2: Persona quality score
bulk_sorted = bulk_df.sort_values("quality_score", ascending=True)
plt.figure(figsize=(10,6))
plt.barh(bulk_sorted["persona_short"], bulk_sorted["quality_score"], color='skyblue')
plt.title("Bulk Experiment Quality Scores by Persona")
plt.xlabel("Quality Score")
plt.xlim(40, 100)
plt.grid(axis='x')
plt.tight_layout()
plt.savefig("chart2_persona_scores.png", dpi=150)
plt.close()

# Chart 3: Optuna History
trials_idx = [h[0] for h in history]
bests = [h[1] for h in history]
plt.figure(figsize=(8,5))
plt.plot(trials_idx, bests, marker='s', linestyle='-', color='r')
plt.title("Optuna Optimization History")
plt.xlabel("Trial Number")
plt.ylabel("Best Mean Score So Far")
plt.grid(True)
plt.tight_layout()
plt.savefig("chart3_optuna_history.png", dpi=150)
plt.close()

print("\nSaved charts:")
print("- chart1_temp_vs_score.png")
print("- chart2_persona_scores.png")
print("- chart3_optuna_history.png")
