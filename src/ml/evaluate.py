"""Evaluate the trained classifier on the labeled dataset.

Run: python -m src.ml.evaluate
"""

import os
import sys

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src.features.extract import FEATURE_NAMES, extract_features
from src.rules.rule_engine import load_whitelist

DATA_PATH = os.path.join(ROOT, "data", "labeled", "commands_labeled.csv")
MODEL_DIR = os.path.join(ROOT, "src", "ml")


def main():
    model = joblib.load(os.path.join(MODEL_DIR, "model.pkl"))
    scaler = joblib.load(os.path.join(MODEL_DIR, "vectorizer.pkl"))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, "labels.pkl"))

    df = pd.read_csv(DATA_PATH)
    whitelist = load_whitelist(os.path.join(ROOT, "config", "whitelist.yaml"))
    X = []
    y_true = []
    for _, row in df.iterrows():
        feats = extract_features(str(row["command"]), whitelist=whitelist)
        X.append([feats[n] for n in FEATURE_NAMES])
        y_true.append(row["label"])

    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)
    y_prob = model.predict_proba(X_scaled)

    print(classification_report(y_true, y_pred, digits=3))
    print("Confusion matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_true, y_pred))

    cols = list(label_encoder.classes_)
    df_res = pd.DataFrame(y_prob, columns=cols)
    df_res["true"] = y_true
    df_res["pred"] = y_pred
    uncertain = df_res[(df_res[cols].max(axis=1) < 0.6)]
    print(f"\nUncertain samples (max prob < 0.6): {len(uncertain)}")


if __name__ == "__main__":
    main()
