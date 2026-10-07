#!/usr/bin/env bash
# SafeShell FULLY AUTOMATIC demo — for recording on ANY laptop with ZERO input.
# Runs start-to-finish, presses Enter by itself, no human needed.
#
# USAGE:
#   bash auto_demo_full.sh            # normal (~4 min, clean screen, 2s gaps)
#   bash auto_demo_full.sh fast       # rehearsal (~2 min)
#
# Setup on the target laptop (only once):
#   pip install -r requirements.txt
#
# Tip: set a clean prompt first so the video shows only "$":
#   PROMPT='$ '
#   bash auto_demo_full.sh
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Auto-detect the Python that has the engine installed.
find_py() {
  local p
  for p in "$HOME/safeshell/cse-venv/bin/python" \
           "$SCRIPT_DIR/.venv/bin/python" \
           "$SCRIPT_DIR/venv/bin/python" \
           "$HOME/.csengine/venv/bin/python" \
           "$(command -v python3)"; do
    if [ -x "$p" ] && "$p" -c "import sys; sys.path.insert(0,'$SCRIPT_DIR'); import src.engine" >/dev/null 2>&1; then
      echo "$p"
      return 0
    fi
  done
  return 1
}

PY="$(find_py)"
if [ -z "$PY" ]; then
  echo "ERROR: no Python with the engine found."
  echo "Install deps first:  pip install -r $SCRIPT_DIR/requirements.txt"
  exit 1
fi

MODE="${1:-normal}"
case "$MODE" in
  fast) PAUSE=2; TYPE_MS=30 ;;
  *)    PAUSE=2; TYPE_MS=110 ;;
esac

PROMPT="\e[1;32m\$\e[0m "

type_cmd() {
  local cmd="$1"
  echo -en "$PROMPT"
  sleep 0.4
  local c r
  while IFS= read -rn1 c; do
    printf '%s' "$c"
    sleep $(( TYPE_MS ))e-3 2>/dev/null || sleep 0.11
    case "$c" in
      " ") sleep 0.15 ;;
      '/'|'|'|'>'|'&') sleep 0.10 ;;
    esac
    r=$(( RANDOM % 20 ))
    if [ "$r" -eq 0 ]; then sleep 0.25; fi
    if [ "$r" -eq 1 ]; then sleep 0.12; fi
  done <<< "$cmd"
  sleep 0.4
  echo ""
}

# 10s countdown to start the screen recorder, then a clean screen.
clear
echo ""
echo "  Recording starts in 10 seconds..."
echo "  (start your screen recorder now, then wait)"
sleep 10
clear

# Scene 1 — watch silently
echo ""
echo "(SafeShell watches silently in the background — you just use your terminal)"
sleep 3

# Scene 2 — everyday commands pass
type_cmd "echo hello"
echo "hello"
type_cmd "ls -la"
ls -la | head -8
sleep "$PAUSE"

# Scene 3 — block rm -rf /
type_cmd 'csengine check "rm -rf /"'
"$PY" "$SCRIPT_DIR/src/main.py" check "rm -rf /"
sleep "$PAUSE"

# Scene 4 — block fork bomb
type_cmd 'csengine check ":(){ :|:& };:"'
"$PY" "$SCRIPT_DIR/src/main.py" check ":(){ :|:& };:"
sleep "$PAUSE"

# Scene 5 — warn chmod 777
type_cmd 'csengine check "chmod -R 777 /var/www"'
"$PY" "$SCRIPT_DIR/src/main.py" check "chmod -R 777 /var/www"
sleep "$PAUSE"

# Scene 6 — THE STAR: transactional undo (clean small folder for full simulation)
DEMOWORK="$HOME/demowork"
rm -rf "$DEMOWORK" && mkdir -p "$DEMOWORK/demo"
echo A > "$DEMOWORK/demo/1.txt" && echo B > "$DEMOWORK/demo/2.txt" && echo C > "$DEMOWORK/demo/3.txt"
type_cmd "mkdir -p demo && echo A > demo/1.txt && echo B > demo/2.txt && echo C > demo/3.txt"
echo "created demo/1.txt demo/2.txt demo/3.txt"
echo ""
type_cmd 'csengine run "rm -rf demo"'
( cd "$DEMOWORK" && echo "y" | "$PY" "$SCRIPT_DIR/src/main.py" run "rm -rf demo" )
echo ""
echo "(the demo/ folder is now DELETED by the risky command)"
echo ""
type_cmd "csengine undo last"
( cd "$DEMOWORK" && "$PY" "$SCRIPT_DIR/src/main.py" undo last )
echo ""
echo -e "demo/1.txt = $(cat "$DEMOWORK/demo/1.txt" 2>/dev/null)"
echo -e "demo/2.txt = $(cat "$DEMOWORK/demo/2.txt" 2>/dev/null)"
echo -e "demo/3.txt = $(cat "$DEMOWORK/demo/3.txt" 2>/dev/null)"
rm -rf "$DEMOWORK"
sleep "$PAUSE"

# Scene 7 — ML generalisation: base64 payload
type_cmd 'csengine check "base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=="'
"$PY" "$SCRIPT_DIR/src/main.py" check 'base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=='
sleep "$PAUSE"

# Scene 8 — local LLM reasons about a novel obfuscated command (the wow)
echo ""
echo "(untrained-obfuscation: the on-device qwen2.5:3b model is generating this explanation — no cloud)"
type_cmd 'csengine check "xxd -r -p <<< 77686f616d69"'
"$PY" "$SCRIPT_DIR/src/main.py" check "xxd -r -p <<< 77686f616d69" || true
sleep "$PAUSE"

# Scene 9 — all offline
echo ""
type_cmd "csengine status"
"$PY" "$SCRIPT_DIR/src/main.py" status
sleep "$PAUSE"

# Scene 10 — close
echo ""
echo "SafeShell: your terminal defends itself — and when it doesn't, it undoes."
echo ""
echo "github.com/Adhi-hub07/command-safety-engine"
echo "Made for C-DAC Secure OS Hackathon 2026 · Track 2: AI at Application Level"
echo ""
echo -e "\e[1;36mDemo complete — every scene ran live, fully offline.\e[0m"
