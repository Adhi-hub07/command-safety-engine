"""Deduplicate and normalise the labeled command dataset.

Removes duplicate commands (a duplicate appears in both train and test splits,
silently inflating accuracy), resolves conflicting labels for the same command
toward the most severe class (safety-first), and normalises the provenance
`source` column to the documented vocabulary:
bash-history | mitre-attack | gtfobins | synthetic

Run after `generate_synthetic.py` and `auto_label_raw.py`:
    python scripts/dedupe_dataset.py
"""

import os

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LABELED_PATH = os.path.join(THIS_DIR, "..", "data", "labeled", "commands_labeled.csv")

SEVERITY = {"safe": 0, "risky": 1, "destructive": 2}
SOURCE_ALIASES = {
    "bash_history": "bash-history",
    "synthetic_risky": "synthetic",
    "synthetic_attack": "synthetic",
    "sysadmin_docs": "synthetic",
}


def main():
    df = pd.read_csv(LABELED_PATH)
    before = len(df)

    df["command"] = df["command"].astype(str).str.strip()
    df = df[df["command"] != ""].copy()

    df["_severity"] = df["label"].map(SEVERITY)
    df = df.sort_values("_severity", ascending=False)
    df = df.drop_duplicates(subset=["command"], keep="first")

    df["source"] = df["source"].map(lambda s: SOURCE_ALIASES.get(str(s).strip(), str(s).strip()))

    df = df.sort_values("label").reset_index(drop=True)
    df = df[["command", "label", "source"]]
    df.to_csv(LABELED_PATH, index=False, encoding="utf-8")

    print(f"Rows before dedupe : {before}")
    print(f"Rows after  dedupe : {len(df)}")
    print(f"Removed            : {before - len(df)}")
    print("Label distribution:")
    for label, count in df["label"].value_counts().items():
        print(f"  {label:<12}: {count}")
    print("Sources:")
    for source, count in df["source"].value_counts().items():
        print(f"  {source:<12}: {count}")


if __name__ == "__main__":
    main()
