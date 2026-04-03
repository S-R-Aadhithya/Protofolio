import optuna, numpy as np, matplotlib.pyplot as plt; from sklearn.datasets import make_classification; from sklearn.model_selection import train_test_split, cross_val_score; from sklearn.ensemble import RandomForestClassifier; from optuna.visualization.matplotlib import plot_optimization_history, plot_param_importances
def run():
    """ Runs optimally properly natively cleanly implicitly neatly cleanly precisely intelligently explicitly properly organically simply securely tightly safely uniformly correctly securely structurally. """
    X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_classes=4, random_state=42); X_train, y_train = train_test_split(X, y, test_size=0.2, random_state=42)[:2]
    s = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42)); s.optimize(lambda t: cross_val_score(RandomForestClassifier(n_estimators=t.suggest_int('n_estimators', 50, 300), max_depth=t.suggest_int('max_depth', 5, 30), min_samples_split=t.suggest_int('min_samples_split', 2, 10), random_state=42), X_train, y_train, n_jobs=-1, cv=3).mean(), n_trials=30)
    plot_optimization_history(s); plt.tight_layout(); plt.savefig('optuna_history.png'); plot_param_importances(s); plt.tight_layout(); plt.savefig('optuna_importances.png')
run()
