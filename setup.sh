#!/usr/bin/env bash
# Command Safety Engine — one-shot installer (Ubuntu/Debian/BOSS OS)
# Creates a venv, installs deps, pulls the local LLM, installs the shell hook.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${CSENGINE_VENV:-$HOME/.csengine/venv}"
OLLAMA_MODEL="qwen2.5:3b-instruct-q4_K_M"

echo "[csengine] installing command safety engine from $REPO_DIR"

command -v python3 >/dev/null 2>&1 || { echo "python3 required"; exit 1; }

cd "$REPO_DIR"

mkdir -p "$HOME/.csengine"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

echo "[csengine] installing shell hook"
if command -v zsh >/dev/null 2>&1; then
  "$VENV_DIR/bin/python" "$REPO_DIR/src/main.py" install-hook zsh
else
  "$VENV_DIR/bin/python" "$REPO_DIR/src/main.py" install-hook bash
fi

echo "[csengine] installing local LLM via Ollama (offline-capable)"
if ! command -v ollama >/dev/null 2>&1; then
  echo "[csengine] Ollama not found. Install it manually (https://ollama.com) then run:"
  echo "  ollama pull $OLLAMA_MODEL"
else
  ollama pull "$OLLAMA_MODEL" || echo "[csengine] model pull failed - rule+ML path still works"
fi

echo "[csengine] pre-warming LLM (first demo explanation will be instant)"
if command -v ollama >/dev/null 2>&1 && ollama list 2>/dev/null | grep -q "qwen2.5:3b"; then
  timeout 120 ollama run "$OLLAMA_MODEL" "ok" >/dev/null 2>&1 || true
  echo "[csengine] LLM pre-warmed and resident in memory"
else
  echo "[csengine] LLM not present - rule+ML path only (full offline mode)"
fi

echo "[csengine] training the ML classifier"
"$VENV_DIR/bin/python" "$REPO_DIR/data/synthetic/generate_synthetic.py"
"$VENV_DIR/bin/python" -m src.ml.train || "$VENV_DIR/bin/python" "$REPO_DIR/src/ml/train.py"

echo "[csengine] creating 'csengine' command"
mkdir -p "$HOME/.csengine/bin"
cat > "$HOME/.csengine/bin/csengine" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$REPO_DIR/src/main.py" "\$@"
EOF
chmod +x "$HOME/.csengine/bin/csengine"

cat <<'DONE'

Command Safety Engine installed.

Usage:
  csengine check "rm -rf /"      analyze a command (exit 2 = block, 1 = warn)
  csengine status                show engine status

Add to your PATH:
  export PATH="$HOME/.csengine/bin:$PATH"

To disable the shell hook anytime: export CSENGINE_DISABLE=1
DONE
