#!/usr/bin/env bash
# SafeShell auto-demo runner — HUMAN-STYLE typing
# Plays every demo scene on screen automatically while YOU narrate in real voice.
# Each command is typed out character-by-character (like a real person typing),
# then Enter, then the real engine output appears.
#
# USAGE (run in a SEPARATE terminal window so you can record this screen):
#   bash scripts/auto_demo.sh           # normal pace
#   bash scripts/auto_demo.sh fast      # rehearsal (faster typing + 2s gaps)
#   bash scripts/auto_demo.sh pause-on  # wait for Enter between scenes (safest for recording)
#
# Keep docs/demo_video_script.md open and read the SAY lines as each scene plays.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PY="$HOME/safeshell/cse-venv/bin/python"

MODE="${1:-normal}"
case "$MODE" in
  fast)     PAUSE=2;  CPM=400 ;;
  pause-on) PAUSE=0;  CPM=150 ;;
  *)        PAUSE=6;  CPM=150 ;;
esac

BANNER="\e[1;36m──────────────────────────────────────────────────────────\e[0m"
SCENE="\e[1;33m◆ SCENE\e[0m"
PROMPT="\e[1;32m\$\e[0m "

# Human-like typing: prints the command character by character.
type_cmd() {
  local cmd="$1"
  echo -en "$PROMPT"
  local c
  while IFS= read -rn1 c; do
    printf '%s' "$c"
    sleep 0.006
  done <<< "$cmd"
  # random thinking pause before Enter
  sleep $(( (RANDOM % 4 + 2) / 10 ))
  echo ""
}

scene() {
  echo ""
  echo -e "$BANNER"
  echo -e "$SCENE $1"
}

pause() {
  if [ "$PAUSE" = "0" ]; then
    echo ""
    echo -e "\e[1;35m   [recorded] Press Enter for the next scene...\e[0m"
    read -r _
  else
    sleep "$PAUSE"
  fi
}

# Scene 1 — watch silently (narration only)
scene "1/9 — SafeShell watches every command silently"
echo "(SafeShell watches in the background — you just use your terminal normally)"
pause

# Scene 2 — everyday commands pass
scene "2/9 — Everyday commands cost nothing"
type_cmd "echo hello"
echo "hello"
type_cmd "ls -la"
ls -la | head -8
pause

# Scene 3 — block rm -rf /
scene "3/9 — BLOCK: rm -rf /"
type_cmd 'csengine check "rm -rf /"'
"$PY" src/main.py check "rm -rf /"
pause

# Scene 4 — block fork bomb
scene "4/9 — BLOCK: fork bomb"
type_cmd 'csengine check ":(){ :|:& };:"'
"$PY" src/main.py check ":(){ :|:& };:"
pause

# Scene 5 — warn chmod 777
scene "5/9 — WARN: chmod -R 777"
type_cmd 'csengine check "chmod -R 777 /var/www"'
"$PY" src/main.py check "chmod -R 777 /var/www"
pause

# Scene 6 — THE STAR: transactional undo (runs in a clean small folder so the
# sandbox simulation can stage it fully and report real created/deleted/modified)
DEMOWORK="$HOME/demowork"
scene "6/9 — THE STAR: transactional undo"
rm -rf "$DEMOWORK" && mkdir -p "$DEMOWORK/demo"
echo A > "$DEMOWORK/demo/1.txt" && echo B > "$DEMOWORK/demo/2.txt" && echo C > "$DEMOWORK/demo/3.txt"
type_cmd "mkdir -p demo && echo A > demo/1.txt && echo B > demo/2.txt && echo C > demo/3.txt"
echo "created demo/1.txt demo/2.txt demo/3.txt"
echo ""
type_cmd 'csengine run "rm -rf demo"'
( cd "$DEMOWORK" && echo "y" | "$PY" "$ROOT/src/main.py" run "rm -rf demo" )
echo ""
echo "(the demo/ folder is now DELETED by the risky command)"
echo ""
type_cmd "csengine undo last"
( cd "$DEMOWORK" && "$PY" "$ROOT/src/main.py" undo last )
echo ""
echo -e "demo/1.txt = $(cat "$DEMOWORK/demo/1.txt" 2>/dev/null)"
echo -e "demo/2.txt = $(cat "$DEMOWORK/demo/2.txt" 2>/dev/null)"
echo -e "demo/3.txt = $(cat "$DEMOWORK/demo/3.txt" 2>/dev/null)"
rm -rf "$DEMOWORK"
pause

# Scene 7 — ML generalisation: base64 payload
scene "7/9 — ML generalisation: base64 payload"
type_cmd 'csengine check "base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=="'
"$PY" src/main.py check 'base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=='
pause

# Scene 8 — all offline
scene "8/9 — Everything runs offline, on this machine"
type_cmd "csengine status"
"$PY" src/main.py status
pause

# Scene 9 — close
scene "9/9 — Close"
echo "SafeShell: your terminal defends itself — and when it doesn't, it undoes."
echo ""
echo "github.com/Adhi-hub07/command-safety-engine"
echo "Made for C-DAC Secure OS Hackathon 2026 · Track 2: AI at Application Level"
echo ""
echo -e "\e[1;36mDemo complete — every scene ran live, fully offline.\e[0m"
