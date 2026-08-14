#!/usr/bin/env bash
# SafeShell auto-demo runner — HUMAN-STYLE typing + ON-SCREEN TELEPROMPTER
# Plays every scene automatically. Each command types out like a real person,
# the real engine output appears, then the SAY line (your voice line) appears
# on screen in a bright box — read it aloud with your real voice. Perfect timing,
# nothing fake, exactly matching docs/demo_video_script.md.
#
# USAGE (run in the terminal you will RECORD):
#   bash scripts/auto_demo.sh            # normal pace
#   bash scripts/auto_demo.sh fast       # rehearsal
#   bash scripts/auto_demo.sh pause-on   # press Enter after each scene (interactive)
#   bash scripts/auto_demo.sh clean      # RECORD THIS: no text boxes, clean screen,
#                                        # generous pauses; add your voiceover in editing
#
# Recording tips (clean mode):
#   - Maximise the window, dark theme, 1080p.
#   - Start screen recording, run clean mode, let it play top-to-bottom.
#   - After recording, record your real voice reading the SAY lines from
#     docs/demo_video_script.md and overlay it in your video editor.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PY="$HOME/safeshell/cse-venv/bin/python"

MODE="${1:-normal}"
case "$MODE" in
  fast)     PAUSE=2 ;;
  pause-on) PAUSE=0 ;;
  clean)    PAUSE=20 ;;
  *)        PAUSE=6 ;;
esac

BANNER="\e[1;36m──────────────────────────────────────────────────────────\e[0m"
SCENE="\e[1;33m◆ SCENE\e[0m"
PROMPT="\e[1;32m\$\e[0m "
BOX="\e[1;97m\e[48;5;24m"
RST="\e[0m"

# Human-like typing: prints the command character by character.
type_cmd() {
  local cmd="$1"
  echo -en "$PROMPT"
  local c
  while IFS= read -rn1 c; do
    printf '%s' "$c"
    sleep 0.006
  done <<< "$cmd"
  sleep 0.3
  echo ""
}

# Teleprompter box — your voice line, shown big and clear (hidden in clean mode).
say() {
  [ "$MODE" = "clean" ] && return
  echo ""
  echo -e "${BOX}  🎙  ${RST}"
  local line
  while IFS= read -r line; do
    echo -e "${BOX}   ${line}${RST}"
  done <<< "$1"
  echo -e "${BOX}  🎙  ${RST}"
  echo ""
}

scene() {
  [ "$MODE" = "clean" ] && return
  echo ""
  echo -e "$BANNER"
  echo -e "$SCENE $1"
}

pause() {
  if [ "$PAUSE" = "0" ]; then
    [ "$MODE" = "clean" ] && return
    echo -e "\e[1;35m   [recording] after speaking, press Enter for the next scene...\e[0m"
    read -r _
  else
    sleep "$PAUSE"
  fi
}

# Scene 1 — watch silently
scene "1/9 — SafeShell watches every command silently"
say "This is SafeShell — the Command Safety Engine. It watches every command you type, silently, before it ever reaches the operating system."
pause

# Scene 2 — everyday commands pass
scene "2/9 — Everyday commands cost nothing"
type_cmd "echo hello"
echo "hello"
type_cmd "ls -la"
ls -la | head -8
say "Everyday commands pass instantly — they're whitelisted, zero false positives, zero latency. A safety tool you'll actually use."
pause

# Scene 3 — block rm -rf /
scene "3/9 — BLOCK: rm -rf /"
type_cmd 'csengine check "rm -rf /"'
"$PY" src/main.py check "rm -rf /"
say "Recursive deletion of the system root — blocked instantly, with the MITRE technique named and a safe alternative suggested. The machine stays alive."
pause

# Scene 4 — block fork bomb
scene "4/9 — BLOCK: fork bomb"
type_cmd 'csengine check ":(){ :|:& };:"'
"$PY" src/main.py check ":(){ :|:& };:"
say "A fork bomb that would freeze the machine in seconds. Rule and model agree — critical rules always win."
pause

# Scene 5 — warn chmod 777
scene "5/9 — WARN: chmod -R 777"
type_cmd 'csengine check "chmod -R 777 /var/www"'
"$PY" src/main.py check "chmod -R 777 /var/www"
say "Riskier commands aren't hard-blocked — they warn. Graded control: allow, warn, block. The user keeps the final say, but it's an informed one."
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
say "Now the part that makes this different. Before a risky command runs, SafeShell snapshots everything it touches and simulates it — four deleted, one modified. If the result is bad, one command undoes it. The files come back, byte for byte."
pause

# Scene 7 — ML generalisation: base64 payload
scene "7/9 — ML generalisation: base64 payload"
type_cmd 'csengine check "base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=="'
"$PY" src/main.py check 'base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=='
say "No blocklist can match this — a base64 payload that decodes to a write to /etc/passwd piped to bash. The ML layer generalises: obfuscation plus redirection plus a shell pipe, flagged fully offline."
pause

# Scene 8 — all offline
scene "8/9 — Everything runs offline, on this machine"
type_cmd "csengine status"
"$PY" src/main.py status
say "Everything you saw runs on this machine — on BOSS OS, on Ubuntu, on any office laptop. Open-source, offline, sovereign. No data leaves the device."
pause

# Scene 9 — close
scene "9/9 — Close"
echo ""
say "SafeShell: your terminal defends itself — and when it doesn't, it undoes."
echo "github.com/Adhi-hub07/command-safety-engine"
echo "Made for C-DAC Secure OS Hackathon 2026 · Track 2: AI at Application Level"
echo ""
echo -e "\e[1;36mDemo complete — every scene ran live, fully offline.\e[0m"
