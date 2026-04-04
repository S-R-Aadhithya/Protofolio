import optuna
import sklearn
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
import matplotlib.pyplot as plt
import pandas as pd

# Creating a mock dataset representing "Resume skill embeddings" mapping to "Job Roles"
X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_classes=4, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Baseline model
baseline_model = RandomForestClassifier(random_state=42)
baseline_model.fit(X_train, y_train)
y_pred_base = baseline_model.predict(X_test)

print("Baseline Accuracy:", accuracy_score(y_test, y_pred_base))
print("Baseline Precision:", precision_score(y_test, y_pred_base, average='weighted'))
print("Baseline Recall:", recall_score(y_test, y_pred_base, average='weighted'))

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

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=30)

print("\nBest trial:")
trial = study.best_trial
print("  Value: ", trial.value)
print("  Params: ")
for key, value in trial.params.items():
    print("    {}: {}".format(key, value))

# Optimized model
optimized_model = RandomForestClassifier(**trial.params, random_state=42)
optimized_model.fit(X_train, y_train)
y_pred_opt = optimized_model.predict(X_test)

print("\nOptimized Accuracy:", accuracy_score(y_test, y_pred_opt))
print("Optimized Precision:", precision_score(y_test, y_pred_opt, average='weighted'))
print("Optimized Recall:", recall_score(y_test, y_pred_opt, average='weighted'))

# Plotting metrics comparison
metrics = ['Accuracy', 'Precision', 'Recall']
base_scores = [accuracy_score(y_test, y_pred_base), 
               precision_score(y_test, y_pred_base, average='weighted'), 
               recall_score(y_test, y_pred_base, average='weighted')]
opt_scores = [accuracy_score(y_test, y_pred_opt), 
              precision_score(y_test, y_pred_opt, average='weighted'), 
              recall_score(y_test, y_pred_opt, average='weighted')]

x = np.arange(len(metrics))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 6))
rects1 = ax.bar(x - width/2, base_scores, width, label='Baseline')
rects2 = ax.bar(x + width/2, opt_scores, width, label='Optimized')

ax.set_ylabel('Scores')
ax.set_title('Model Performance Comparison (Baseline vs Optuna Optimized)')
ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.legend()
plt.ylim(0.5, 1.0)
plt.savefig('optimization_results.png')
print("Plot saved to optimization_results.png")
