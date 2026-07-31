"""Train the RandomForest command-risk classifier.

Run: python -m src.ml.train
Outputs: src/ml/model.pkl, src/ml/vectorizer.pkl, src/ml/labels.pkl
"""

import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src.features.extract import FEATURE_NAMES, extract_features
from src.rules.rule_engine import load_whitelist

DATA_PATH = os.path.join(ROOT, "data", "labeled", "commands_labeled.csv")
MODEL_DIR = os.path.join(ROOT, "src", "ml")


def load_dataset():
    df = pd.read_csv(DATA_PATH)
    whitelist = load_whitelist(os.path.join(ROOT, "config", "whitelist.yaml"))
    rows = []
    for _, row in df.iterrows():
        feats = extract_features(str(row["command"]), whitelist=whitelist)
        rows.append({"label": row["label"], **feats})
    return pd.DataFrame(rows)


def main():
    data = load_dataset()
    X = data[FEATURE_NAMES].values
    y = data["label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred, digits=3))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    label_encoder = LabelEncoder()
    label_encoder.fit(y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "vectorizer.pkl"))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, "labels.pkl"))
    print(f"Saved model to {MODEL_DIR}")


if __name__ == "__main__":
    main()
