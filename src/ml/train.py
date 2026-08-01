"""Train the GradientBoosting command-risk classifier.

Pipeline:
    1. Load the labeled commands, extract the 20-feature vector per command
       (src/features/extract.py) with the production whitelist.
    2. Run 5-fold stratified cross-validation on the FULL dataset to report
       per-fold accuracy, macro-F1, and destructive-class recall (mean +/- std).
    3. Fit the production model on the final 80/20 stratified split (seed 42)
       and evaluate on the held-out test set (per-class table + confusion matrix).
    4. Persist model.pkl, vectorizer.pkl (StandardScaler), labels.pkl.

GradientBoosting is the deployed model: on the deduplicated dataset it beats
RandomForest on both macro-F1 and destructive-class recall (see src/ml/compare.py).

Run: python -m src.ml.train
Outputs: src/ml/model.pkl, src/ml/vectorizer.pkl, src/ml/labels.pkl
"""

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src.features.extract import FEATURE_NAMES, extract_features
from src.rules.rule_engine import load_whitelist

DATA_PATH = os.path.join(ROOT, "data", "labeled", "commands_labeled.csv")
MODEL_DIR = os.path.join(ROOT, "src", "ml")

RANDOM_STATE = 42
N_SPLITS = 5
DESTRUCTIVE_LABEL = "destructive"

MODEL_PARAMS = {
    "n_estimators": 200,
    "max_depth": 4,
    "random_state": RANDOM_STATE,
}


def load_dataset():
    df = pd.read_csv(DATA_PATH)
    whitelist = load_whitelist(os.path.join(ROOT, "config", "whitelist.yaml"))
    rows = []
    for _, row in df.iterrows():
        feats = extract_features(str(row["command"]), whitelist=whitelist)
        rows.append({"label": row["label"], **feats})
    return pd.DataFrame(rows)


def run_cross_validation(X, y, classes, n_splits=N_SPLITS):
    """5-fold stratified CV. Returns (mean_acc, mean_macro_f1, mean_destructive_recall)."""
    destructive_idx = list(classes).index(DESTRUCTIVE_LABEL) if DESTRUCTIVE_LABEL in classes else None

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    accs, f1s, recalls = [], [], []

    print("=" * 70)
    print(f"{n_splits}-Fold Stratified Cross-Validation (GradientBoosting)")
    print("=" * 70)
    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y), start=1):
        model = GradientBoostingClassifier(**MODEL_PARAMS)
        model.fit(X[train_idx], y[train_idx])
        y_pred = model.predict(X[val_idx])

        acc = accuracy_score(y[val_idx], y_pred)
        macro = f1_score(y[val_idx], y_pred, average="macro", zero_division=0)
        accs.append(acc)
        f1s.append(macro)

        recall_str = "N/A"
        if destructive_idx is not None:
            _, recall, _, _ = precision_recall_fscore_support(
                y[val_idx], y_pred, labels=classes, zero_division=0
            )
            recalls.append(recall[destructive_idx])
            recall_str = f"{recall[destructive_idx]:.4f}"

        print(
            f"Fold {fold_idx}/{n_splits} | Accuracy: {acc:.4f} | "
            f"Macro-F1: {macro:.4f} | Destructive Recall: {recall_str}"
        )

    print("-" * 70)
    print(f"Mean Accuracy        : {np.mean(accs):.4f} +/- {np.std(accs):.4f}")
    print(f"Mean Macro-F1        : {np.mean(f1s):.4f} +/- {np.std(f1s):.4f}")
    if recalls:
        print(f"Mean Destructive Recall: {np.mean(recalls):.4f} +/- {np.std(recalls):.4f}")
    print("=" * 70)
    return np.mean(accs), np.mean(f1s), (np.mean(recalls) if recalls else None)


def train_final_model(X, y, classes):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = GradientBoostingClassifier(**MODEL_PARAMS)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    print("\nFinal Held-Out Test Set Evaluation (80/20 split, seed=42)")
    print("=" * 70)
    print(f"Test Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Test Macro-F1 : {f1_score(y_test, y_pred, average='macro', zero_division=0):.4f}")
    print("\nPer-class metrics (rows=true, cols=pred):")
    print(classification_report(y_test, y_pred, labels=classes, digits=3))
    print("Confusion matrix:")
    print(f"  Classes: {list(classes)}")
    print(confusion_matrix(y_test, y_pred, labels=classes))
    print("=" * 70)
    return model, scaler


def main():
    data = load_dataset()
    X = data[FEATURE_NAMES].values
    y = data["label"].values
    classes = np.array(sorted(set(y)))

    print(f"Loaded {len(data)} labeled commands from {os.path.basename(DATA_PATH)}")
    print(f"Classes: {list(classes)}")
    print(f"Label distribution: {dict(pd.Series(y).value_counts())}\n")

    run_cross_validation(X, y, classes)

    model, scaler = train_final_model(X, y, classes)

    label_encoder = LabelEncoder()
    label_encoder.fit(y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "vectorizer.pkl"))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, "labels.pkl"))
    print(f"Saved model/vectorizer/labels to {MODEL_DIR}")


if __name__ == "__main__":
    main()
