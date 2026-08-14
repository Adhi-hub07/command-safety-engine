#!/usr/bin/env bash
# SafeShell auto-demo runner
# Plays every demo scene on screen automatically while YOU narrate the script.
# Usage:
#   bash scripts/auto_demo.sh             # full run, auto-pause between scenes
#   bash scripts/auto_demo.sh fast        # short pauses (for rehearsal)
#   bash scripts/auto_demo.sh pause-on    # wait for Enter between scenes
#
# Keep docs/demo_video_script.md open next to the camera and read the SAY lines.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PY="$HOME/safeshell/cse-venv/bin/python"

MODE="${1:-normal}"
case "$MODE" in
  fast)     PAUSE=2 ;;
  pause-on) PAUSE=0 ;;
  *)        PAUSE=6 ;;
esac

BANNER="\e[1;36m──────────────────────────────────────────────────────────\e[0m"
SCENE="\e[1;33mSCENE\e[0m"
TYP="\e[1;32m▶\e[0m"

pause() {
  if [ "$PAUSE" = "0" ]; then
    echo ""
    echo -e "\e[1;35m   Press Enter to continue to the next scene...\e[0m"
    read -r _
  else
    sleep "$PAUSE"
  fi
}

# Scene 1 — watch silently
echo -e "$BANNER"
echo -e "$SCENE 1/9 — SafeShell watches every command silently"
echo -e "$TYP you just type any command — nothing slows down"
echo "(no output — SafeShell watches silently in the background)"
pause

# Scene 2 — everyday commands pass
echo -e "$BANNER"
echo -e "$SCENE 2/9 — Everyday commands cost nothing"
echo -e "$TYP echo hello"
echo "hello"
echo -e "$TYP ls -la"
ls -la
pause

# Scene 3 — block rm -rf /
echo -e "$BANNER"
echo -e "$SCENE 3/9 — BLOCK: rm -rf /"
echo -e "$TYP csengine check \"rm -rf /\""
"$PY" src/main.py check "rm -rf /"
pause

# Scene 4 — block fork bomb
echo -e "$BANNER"
echo -e "$SCENE 4/9 — BLOCK: fork bomb"
echo -e "$TYP csengine check \":(){ :|:& };:\""
"$PY" src/main.py check ":(){ :|:& };:"
pause

# Scene 5 — warn chmod 777
echo -e "$BANNER"
echo -e "$SCENE 5/9 — WARN: chmod -R 777"
echo -e "$TYP csengine check \"chmod -R 777 /var/www\""
"$PY" src/main.py check "chmod -R 777 /var/www"
pause

# Scene 6 — THE STAR: transactional undo
# (runs in a clean small folder so the sandbox simulation can stage it fully)
DEMOWORK="$HOME/demowork"
echo -e "$BANNER"
echo -e "$SCENE 6/9 — THE STAR: transactional undo"
echo -e "$TYP mkdir -p demo && echo A > demo/1.txt && echo B > demo/2.txt && echo C > demo/3.txt"
rm -rf "$DEMOWORK" && mkdir -p "$DEMOWORK/demo"
echo A > "$DEMOWORK/demo/1.txt" && echo B > "$DEMOWORK/demo/2.txt" && echo C > "$DEMOWORK/demo/3.txt"
echo "created demo/1.txt demo/2.txt demo/3.txt"
echo ""
echo -e "$TYP csengine run \"rm -rf demo\""
( cd "$DEMOWORK" && echo "y" | "$PY" "$ROOT/src/main.py" run "rm -rf demo" )
echo ""
echo "demo/ folder is now DELETED by the risky command."
echo -e "$TYP csengine undo last"
( cd "$DEMOWORK" && "$PY" "$ROOT/src/main.py" undo last )
echo ""
echo -e "demo/1.txt = $(cat "$DEMOWORK/demo/1.txt" 2>/dev/null)"
echo -e "demo/2.txt = $(cat "$DEMOWORK/demo/2.txt" 2>/dev/null)"
echo -e "demo/3.txt = $(cat "$DEMOWORK/demo/3.txt" 2>/dev/null)"
rm -rf "$DEMOWORK"
pause

# Scene 7 — ML generalisation: base64 payload
echo -e "$BANNER"
echo -e "$SCENE 7/9 — ML generalisation: base64 payload"
echo -e "$TYP csengine check 'base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=='"
"$PY" src/main.py check 'base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=='
pause

# Scene 8 — all offline
echo -e "$BANNER"
echo -e "$SCENE 8/9 — Everything runs offline, on this machine"
echo -e "$TYP csengine status"
"$PY" src/main.py status
pause

# Scene 9 — close
echo -e "$BANNER"
echo -e "$SCENE 9/9 — Close"
echo -e "SafeShell: your terminal defends itself — and when it doesn't, it undoes."
echo -e "github.com/Adhi-hub07/command-safety-engine"
echo -e "Made for C-DAC Secure OS Hackathon 2026 · Track 2: AI at Application Level"
echo -e "$BANNER"
echo ""
echo -e "\e[1;36mDemo complete — all scenes ran live on this machine, fully offline.\e[0m"
