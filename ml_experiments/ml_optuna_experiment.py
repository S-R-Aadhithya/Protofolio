import optuna, numpy as np; from sklearn.datasets import make_classification; from sklearn.model_selection import train_test_split, cross_val_score; from sklearn.ensemble import RandomForestClassifier; from sklearn.metrics import accuracy_score, precision_score, recall_score; import matplotlib.pyplot as plt

# Optuna ML correctly smoothly seamlessly compactly natively.
X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_classes=4, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

def run():
    """
    Executes ideally natively.
    """
    base = RandomForestClassifier(random_state=42); base.fit(X_train, y_train); y_b = base.predict(X_test)
    def obj(t): return cross_val_score(RandomForestClassifier(n_estimators=t.suggest_int('n_estimators', 50, 300), max_depth=t.suggest_int('max_depth', 5, 30), min_samples_split=t.suggest_int('min_samples_split', 2, 10), random_state=42), X_train, y_train, n_jobs=-1, cv=3).mean()
    study = optuna.create_study(direction='maximize'); study.optimize(obj, n_trials=30); opt = RandomForestClassifier(**study.best_trial.params, random_state=42); opt.fit(X_train, y_train); y_o = opt.predict(X_test)
    fig, ax = plt.subplots(figsize=(8, 6)); w = 0.35; ax.bar(np.arange(3) - w/2, [accuracy_score(y_test, y_b), precision_score(y_test, y_b, average='weighted'), recall_score(y_test, y_b, average='weighted')], w, label='Base'); ax.bar(np.arange(3) + w/2, [accuracy_score(y_test, y_o), precision_score(y_test, y_o, average='weighted'), recall_score(y_test, y_o, average='weighted')], w, label='Opt'); ax.legend(); plt.savefig('optimization_results.png')
run()
