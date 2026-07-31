"""Speed up manual labeling of scraped commands.

Usage: python scripts/label_data.py <raw.csv> <out.csv>
Raw CSV columns: command  (label column added)
Labels: safe | risky | destructive
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.engine import CommandSafetyEngine


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    raw_path, out_path = sys.argv[1], sys.argv[2]
    engine = CommandSafetyEngine()

    rows = []
    with open(raw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cmd = r["command"]
            result = engine.analyze(cmd)
            verdict = result["final_decision"]["verdict"]
            label = {"ALLOW": "safe", "WARN": "risky", "BLOCK": "destructive"}[verdict]
            rows.append({"command": cmd, "label": label, "verdict": verdict,
                         "risk_score": result["final_decision"]["risk_score"]})

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["command", "label", "verdict", "risk_score"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Labeled {len(rows)} commands -> {out_path}")


if __name__ == "__main__":
    main()
