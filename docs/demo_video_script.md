# Demo Video Script — SafeShell (Command Safety Engine) — ~4 min, one take

> Record on a clean **Ubuntu 24.04 or BOSS OS VM** (4 GB RAM, 2 vCPU). Maximise
> one terminal, dark theme, 1080p. No cuts needed. If you flub a line, pause 2 s
> and re-take from the start of that scene.
>
> **The output blocks below are the REAL engine output — copy them from here so
> what you type matches what you see.** Do not fake output.
>
> End card: repo URL + "SafeShell · Made for C-DAC Secure OS Hackathon 2026 · Track 2: AI at Application Level".

---

## Before recording (5 min, not on camera)

```bash
git clone https://github.com/Adhi-hub07/command-safety-engine
cd command-safety-engine
bash setup.sh && source ~/.bashrc
csengine status        # 27 rules loaded, ML model loaded
bash scripts/verify_demo.sh   # 17 passed
```

Sanity tip: run each command below once **before** recording so you know the
exact output. Keep this cheat sheet open next to the camera.

---

## Scene 1 — Watch every command silently (0:00–0:25)

**TYPE**
```bash
echo hello
```

**YOU WILL SEE** (looks like nothing — that's the point)

**SAY**
> "This is SafeShell — the Command Safety Engine. It watches every command you
> type, silently, before it ever reaches the operating system."

---

## Scene 2 — Everyday commands cost nothing (0:25–0:45)

**TYPE**
```bash
git status
ls -la
cd ~
```

**YOU WILL SEE** normal output, instant, no warnings.

**SAY**
> "Everyday commands pass instantly — they're whitelisted, zero false
> positives, zero latency. A safety tool you'll actually use."

---

## Scene 3 — Block: `rm -rf /` (0:45–1:15)

**TYPE**
```bash
csengine check "rm -rf /"
```

**YOU WILL SEE**
```
Verdict            BLOCK
Risk score         100/100
Matched rule       R001_ROOT_DELETE
MITRE              T1485
Safer alternative  rm -rf /path/to/specific/folder
```

**SAY**
> "Recursive deletion of the system root — blocked instantly, with the MITRE
> technique named and a safe alternative suggested. The machine stays alive."

---

## Scene 4 — Block: fork bomb (1:15–1:35)

**TYPE**
```bash
csengine check ":(){ :|:& };:"
```

**YOU WILL SEE**
```
Verdict            BLOCK
Risk score         100/100
Matched rule       R008_FORK_BOMB
```

**SAY**
> "A fork bomb that would freeze the machine in seconds. Rule and model agree —
> critical rules always win."

---

## Scene 5 — Warn, don't block: `chmod -R 777` (1:35–2:00)

**TYPE**
```bash
csengine check "chmod -R 777 /var/www"
```

**YOU WILL SEE**
```
Verdict            WARN
Risk score         60/100
Matched rule       R007_PERMISSIONS_777
```

**SAY**
> "Riskier commands aren't hard-blocked — they warn. Graded control:
> allow, warn, block. The user keeps the final say, but it's an informed one."

---

## Scene 6 — THE STAR: transactional undo (2:00–2:50)

> This is the headline of our problem statement. Make it count.

**TYPE** (this creates 3 fake files, deletes them safely, then restores them)
```bash
mkdir -p demo && echo A > demo/1.txt && echo B > demo/2.txt && echo C > demo/3.txt
csengine run "rm -rf demo"
```

**YOU WILL SEE**
```
Verdict        WARN
Undo plan      restore .../demo from snapshot
Simulation     4 deleted · 1 modified · 0 created
Run `rm -rf demo` with an automatic undo snapshot? [y/N]
```

**TYPE** `y` and press Enter. The files are deleted.

**TYPE**
```bash
csengine undo last
```

**YOU WILL SEE** the files back.

**SAY**
> "Now the part that makes this different. Before a risky command runs,
> SafeShell snapshots everything it touches and simulates it — '4 deleted,
> 1 modified'. If the result is bad, one command undoes it. The files come
> back, byte for byte."

---

## Scene 7 — ML generalisation: base64 payload (2:50–3:15)

**TYPE**
```bash
csengine check 'base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA=='
```

**YOU WILL SEE**
```
Verdict            WARN
Risk score         60/100
ML prediction      risky
```

**SAY**
> "No blocklist can match this — a base64 payload that decodes to a write to
> /etc/passwd piped to bash. The ML layer generalises: obfuscation plus
> redirection plus a shell pipe, flagged fully offline."

---

## Scene 8 — All offline (3:15–3:40)

**TYPE**
```bash
csengine status
```

**YOU WILL SEE**
```
csengine 1.1.0
Rule engine  : 27 rules loaded
ML model     : loaded
LLM (Ollama) : running (qwen2.5:3b)
Whitelist    : 87 safe patterns
```

**SAY**
> "Everything you saw runs on this machine — on BOSS OS, on Ubuntu, on any
> office laptop. Open-source, offline, sovereign. No data leaves the device."

---

## Scene 9 — Close (3:40–3:55)

**SAY**
> "SafeShell: your terminal defends itself — and when it doesn't, it undoes."

**SHOW** end card: `github.com/Adhi-hub07/command-safety-engine` ·
"Made for C-DAC Secure OS Hackathon 2026 · Track 2: AI at Application Level".

---

## On-camera failure cheat sheet

| If you see | Just do |
|---|---|
| `csengine: command not found` | `source ~/.bashrc` and re-type the command |
| ML line missing in `status` | `python src/ml/train.py` first |
| LLM says "server down" | LLM is optional — cut scene 7's explanation line or skip it |
| `undo last` says nothing to undo | the demo files were deleted by an earlier take — re-run the `mkdir` line |
| `verify_demo.sh` not 17 passed | **do not record** until it passes |

## What the judge will check

- `bash scripts/verify_demo.sh` → 17 passed
- `csengine status` → 27 rules, model loaded
- repo private + `ssm-hackathon` collaborator before submission
