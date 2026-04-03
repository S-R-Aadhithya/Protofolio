import optuna
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from optuna.visualization.matplotlib import plot_optimization_history, plot_param_importances

X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_classes=4, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

def objective(trial):
    n_estimators = trial.suggest_int('n_estimators', 50, 300)
    max_depth = trial.suggest_int('max_depth', 5, 30)
    min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
    
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=42
    )
    return cross_val_score(clf, X_train, y_train, n_jobs=-1, cv=3).mean()

# Note: We use a fixed seed to make this reproducible for the chart
sampler = optuna.samplers.TPESampler(seed=42)
study = optuna.create_study(direction='maximize', sampler=sampler)
study.optimize(objective, n_trials=30)

print(f"Best Trial: {study.best_trial.number}")
print(f"Best Params: {study.best_params}")

fig1 = plot_optimization_history(study)
plt.tight_layout()
plt.savefig('optuna_history.png')
print("optuna_history.png saved.")

fig2 = plot_param_importances(study)
plt.tight_layout()
plt.savefig('optuna_importances.png')
print("optuna_importances.png saved.")

importances = optuna.importance.get_param_importances(study)
print("Importances:")
for key, val in importances.items():
    print(f"{key}: {val:.4f}")
