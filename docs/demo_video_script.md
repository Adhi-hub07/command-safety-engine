# Demo Video Script — Command Safety Engine (~4 minutes, one take)

> Record with OBS or `asciinema` on a clean **Ubuntu 24.04 or BOSS OS VM**
> (4 GB RAM, 2 vCPU). Maximise one terminal, dark theme, 1080p. No cuts needed —
> but if you flub a line, pause 2 s and re-take from the start of the scene.
> Optional end card with the repo URL.
>
> All commands below show the **actual** engine output (captured from a Kali VM,
> same code that is pushed). Do not fake output — judges run `verify_demo.sh`.

---

## 0. Pre-flight checklist (before recording)

```bash
git clone <repo-url> && cd command-safety-engine
bash setup.sh                 # venv + deps + model training + Ollama + hooks
source ~/.bashrc
csengine status               # MUST show: 27 rules, ML model loaded
# if LLM line says "server down", start it:
ollama serve &   # then: ollama pull qwen2.5:3b-instruct-q4_K_M
```

Sanity check before rolling:

```bash
bash scripts/verify_demo.sh   # expect: RESULT: 17 passed, 0 failed
```

---

## 1. Timing map (total 4:00)

| # | Scene | Duration | Video time |
|---|-------|----------|------------|
| 1 | Hook-in-action (silent watch) | 20 s | 0:00–0:20 |
| 2 | Daily commands pass instantly | 25 s | 0:20–0:45 |
| 3 | Destructive block: `rm -rf /` | 30 s | 0:45–1:15 |
| 4 | Fork bomb block | 20 s | 1:15–1:35 |
| 5 | Risky warn: `chmod -R 777` | 25 s | 1:35–2:00 |
| 6 | ML generalisation: base64 payload | 30 s | 2:00–2:30 |
| 7 | LLM explanation (Ollama on) | 35 s | 2:30–3:05 |
| 8 | Audit log, hashed | 25 s | 3:05–3:30 |
| 9 | Status: all offline | 20 s | 3:30–3:50 |
| 10 | Close / end card | 10 s | 3:50–4:00 |

---

## 2. Scene-by-scene

### Scene 1 — Hook-in-action (0:00–0:20)

Type (nothing visibly happens — that's the point):

```bash
$ echo hello
hello
```

**Narration (15 s):** "This is the Command Safety Engine. It watches every
command you type, silently, before that command ever reaches the operating
system."

### Scene 2 — Daily commands pass instantly (0:20–0:45)

```bash
$ git status
On branch main
nothing to commit, working tree clean
$ ls -la
total 72
drwxr-xr-x 13 kali kali  4096 ...
$ cd ~
```

**Narration (15 s):** "Everyday commands cost you nothing. They're whitelisted,
so they skip analysis entirely — zero false positives, zero latency. This is
what makes a safety tool actually usable."

### Scene 3 — Destructive block: `rm -rf /` (0:45–1:15)

```bash
$ rm -rf /
[BLOCKED] recursive delete of system root   (R001, MITRE T1485)
  Risk: 100/100
  Suggested safe alternative:  rm -rf /path/to/folder
```

**Expected real output:** verdict BLOCK, risk 100, rule R001_ROOT_DELETE.
Exit code 2 (type `echo $?` → `2`).

**Narration (20 s):** "Now a recursive deletion of the system root. The rule
engine blocks it instantly, shows why, names the MITRE technique, and — this is
important — suggests a safe alternative. The user stays in control; the system
stays alive."

### Scene 4 — Fork bomb (1:15–1:35)

```bash
$ :(){ :|:& };:
[BLOCKED] fork bomb detected   (R008, MITRE T1498)
  Risk: 100/100
```

**Narration (15 s):** "A fork bomb that would otherwise freeze the machine in
seconds. Recognised by rule and model together. Critical rules always win — the
machine can't be talked out of a block."

### Scene 5 — Risky warn: `chmod -R 777` (1:35–2:00)

```bash
$ chmod -R 777 /var/www
[WARN] world-writable permissions   (R007)
  Risk: 60/100
  Continue? [y/N]
```

Type `n`.

**Narration (15 s):** "Riskier commands aren't hard-blocked — they warn and ask
for confirmation. Graded control: allow, warn, block. The user always has the
final say, but now the say is an *informed* one."

### Scene 6 — ML generalisation: base64 payload (2:00–2:30)

```bash
$ base64 -d <<< cHJpbnRmIGhhY2tlZCA+IC9ldGMvcGFzc3dkIHwgYmFzaA==
[WARN] obfuscated payload decoded to a write-to-/etc/passwd pipe   (ML)
  Risk: 60/100   (matched rule: none — flagged by ML)
```

**Narration (15 s):** "This is the attack no blocklist string can match — a
base64-encoded payload that, once decoded, writes to /etc/passwd and pipes to
bash. No rule in our file matches it. The machine-learning layer generalises:
obfuscation plus redirection plus a shell pipe — it's risky, and it's flagged,
fully offline."

### Scene 7 — LLM explanation (2:30–3:05)

Make sure Ollama is running and `csengine status` shows LLM available. Type an
ambiguous-but-harmless command that triggers the LLM path:

```bash
$ xxd -r -p <<< '77686f616d69'
[WARN] this decodes hex text "whoami" — a read-only command
  Explanation (local Qwen 2.5 3B): this command reverses a hex-encoded
  string. It is obfuscation, which is how malware hides, but the payload
  itself only runs `whoami`. Proceed with care.
```

**Narration (20 s):** "When a command is genuinely confusing, a local Qwen 2.5
model — running entirely on this laptop — writes a plain-language explanation.
No cloud. No network. The judgement never depends on a server that might be
down."

### Scene 8 — Audit log, hashed (3:05–3:30)

```bash
$ cat ~/.csengine/audit.log
{..., "cmd_sha256": "a3f2...", "verdict": "BLOCK", "rule": "R001"}
{..., "cmd_sha256": "9b1c...", "verdict": "WARN",  "rule": "R007"}
```

**Narration (15 s):** "Every decision is written to an audit log. Commands are
stored only as hashes, so an administrator can reconstruct what happened without
storing your plaintext commands — privacy and forensics at the same time."

### Scene 9 — Status: all offline (3:30–3:50)

```bash
$ csengine status
csengine 1.0.0
Rule engine  : 27 rules loaded
ML model     : loaded
LLM (Ollama) : running (qwen2.5:3b)
Whitelist    : 87 safe patterns
```

**Narration (15 s):** "Everything you've seen runs on this machine — on BOSS OS,
on Ubuntu, on any office laptop. Open-source, offline, sovereign. No data leaves
the device."

### Scene 10 — Close (3:50–4:00)

**Narration (10 s):** "Command Safety Engine: your terminal defends itself."
End card: repo URL, "Made for C-DAC Secure OS Hackathon 2026 · Track 2".

---

## 3. Failure fallbacks (if something misbehaves on camera)

| Symptom | Fix |
|---|---|
| `status` says ML not loaded | model trains in `setup.sh`; if missing run `python src/ml/train.py` |
| LLM line says server down | LLM is optional; re-take scene 7 after `ollama serve` or cut scene 7 |
| A safe command WARNs on camera | it's honest behaviour — keep it, the narration covers grading |
| `verify_demo.sh` not 17/17 | do not record until it is |

## 4. What the judge will check (so do not script over these)

- `git ls-remote` matches the submitted commit (repo frozen at Stage-1 deadline)
- `bash scripts/verify_demo.sh` → 17 passed
- `csengine status` → 27 rules, model loaded
- repo private + `ssm-hackathon` collaborator present before submission
