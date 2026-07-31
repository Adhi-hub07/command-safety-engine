"""Model comparison: RandomForest vs GradientBoosting vs LogisticRegression.

Trains each model on the same labeled dataset with identical 80/20 stratified
split and reports accuracy, macro-F1 and per-class recall, so the final model
choice is defensible in front of judges.

Usage:
  python src/ml/compare.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, recall_score
from sklearn.model_selection import train_test_split

from src.features.extract import FEATURE_NAMES, extract_features, feature_vector
from src.rules.rule_engine import load_whitelist

DATA_PATH = os.path.join(ROOT, "data", "labeled", "commands_labeled.csv")
WHITELIST_PATH = os.path.join(ROOT, "config", "whitelist.yaml")

MODELS = {
    "RandomForest": RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1
    ),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42),
    "LogisticRegression": LogisticRegression(max_iter=2000, random_state=42),
}


def load_dataset():
    df = pd.read_csv(DATA_PATH)
    whitelist = load_whitelist(WHITELIST_PATH)
    rows = []
    for _, row in df.iterrows():
        feats = extract_features(str(row["command"]), whitelist=whitelist)
        rows.append(feature_vector(feats))
    X = np.asarray(rows, dtype=float)
    y = df["label"].values
    return X, y


def main():
    X, y = load_dataset()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    print(f"Dataset : {len(y)} commands from {DATA_PATH}")
    print(f"Split   : train={len(y_tr)} test={len(y_te)} (stratified, seed 42)\n")

    print(f"{'Model':<20}{'Acc':>8}{'Macro-F1':>10}{'Recall destructive':>20}{'Recall risky':>14}{'Recall safe':>12}")
    results = {}
    for name, model in MODELS.items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        acc = accuracy_score(y_te, pred)
        macro = f1_score(y_te, pred, average="macro")
        recall = recall_score(y_te, pred, average=None, labels=sorted(set(y_te)))
        results[name] = {"accuracy": acc, "macro_f1": macro, "recall": dict(zip(sorted(set(y_te)), recall))}
        r = results[name]["recall"]
        print(
            f"{name:<20}{acc:>8.4f}{macro:>10.4f}"
            f"{r.get('destructive', float('nan')):>20.4f}"
            f"{r.get('risky', float('nan')):>14.4f}"
            f"{r.get('safe', float('nan')):>12.4f}"
        )

    print("\nBest by macro-F1:", max(results, key=lambda k: results[k]["macro_f1"]))
    best = max(results, key=lambda k: results[k]["macro_f1"])
    print("\nFull classification report for", best)
    best_model = MODELS[best]
    best_model.fit(X_tr, y_tr)
    print(classification_report(y_te, best_model.predict(X_te), digits=3))

    feature_importance = np.argsort(-best_model.feature_importances_)[:10]
    print(f"Top features ({best} importance):")
    for i, idx in enumerate(feature_importance, 1):
        print(f"  {i:>2}. {FEATURE_NAMES[idx]:<32} {best_model.feature_importances_[idx]:.4f}")


if __name__ == "__main__":
    main()
