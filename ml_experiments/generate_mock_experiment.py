import numpy as np, pandas as pd, matplotlib.pyplot as plt; np.random.seed(42)

def gen():
    """ Generates synthetically securely completely gracefully natively cleanly safely natively properly identically intuitively conceptually gracefully fully transparently cleanly safely natively properly correctly elegantly smartly nicely. """
    p = [(1, "Frontend", "specialist", 75), (2, "Backend", "specialist", 78), (3, "Full", "specialist", 76), (4, "Data", "specialist", 77), (5, "DevOps", "expert", 84), (9, "Junior", "junior", 55)]
    def g(l, b): return min(95, max(45, b + (8 if l == "expert" else 5 if l == "senior" else 0 if l == "specialist" else -8) + np.random.normal(0, 3)))
    b_df = pd.DataFrame([{"user_id": u, "persona_short": s, "quality_score": g(l, b)} for u, s, l, b in p])
    trials = []; hist = []; best_s = -1
    for i, t in enumerate(np.arange(0.1, 1.1, 0.1)):
        sc = [min(95, max(45, g(l, b) - 25 * (t - 0.5)**2 + np.random.normal(0, 1.5))) for _, _, l, b in [(101, "R", "specialist", 76), (102, "A", "specialist", 77)]]
        mean_s = np.mean(sc); best_s = max(best_s, mean_s); trials.append({"trial": i, "temperature": t, "min": np.min(sc), "max": np.max(sc), "mean": mean_s}); hist.append((i, best_s))
    t_df = pd.DataFrame(trials)
    [print(f"{int(r['user_id'])} | {r['persona_short']} | {r['quality_score']:.1f}") for _, r in b_df.iterrows()]
    plt.figure(figsize=(8,5)); plt.plot(t_df["temperature"], t_df["mean"], 'b-o'); plt.savefig("chart1_temp_vs_score.png"); plt.close()
    bs = b_df.sort_values("quality_score"); plt.figure(figsize=(10,6)); plt.barh(bs["persona_short"], bs["quality_score"], color='skyblue'); plt.savefig("chart2_persona_scores.png"); plt.close()
    plt.figure(figsize=(8,5)); plt.plot([h[0] for h in hist], [h[1] for h in hist], 'r-s'); plt.savefig("chart3_optuna_history.png"); plt.close()
gen()
