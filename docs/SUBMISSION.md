# Command Safety Engine — C-DAC Secure OS Hackathon 2026 Submission

**Track:** AI @ Application Level (sub-problem: Command Safety)
**Target OS:** Ubuntu 22.04/24.04, BOSS Linux
**Status:** code complete — all 22 tests passing, model trained, demo-ready

---

## 1. Abstract (300 words, submission-portal ready)

Every day, users type dangerous commands into a terminal — `rm -rf /`, fork bombs,
`chmod -R 777`, "download-and-run" chains — often once, fatally. Yet no mainstream
operating system ships a safety layer between the keyboard and the kernel. This
project, **Command Safety Engine (csengine)**, is a fully offline, on-device AI
guardian for the shell: it intercepts every command the user types, decides in
milliseconds whether it is **safe**, **risky**, or **destructive**, and asks for
confirmation before anything harmful reaches the operating system.

The engine is a three-layer defence-in-depth pipeline. **Layer 1** is a curated
deterministic rule engine of 20 MITRE ATT&CK-aligned rule groups (recursive
root deletion, fork bombs, permission escalation, credential scraping, supply-chain
"download-and-run", network recon, obfuscation, and more), each with human-readable
explanations and safe alternatives. **Layer 2** is a RandomForest machine-learning
classifier trained on 1,149 synthetic attack/benign shell commands (90.9% accuracy,
0.90 macro F1) that generalises to novel commands no rule covers. **Layer 3** is a
local LLM (Qwen 2.5 3B via Ollama) invoked only for genuinely ambiguous commands,
writing natural-language explanations in the user's language. Every decision is
audited to a hashed, privacy-preserving log.

Everything runs 100% offline on commodity hardware. Rule+ML checks complete in
under 1 ms; the full pipeline averages 56 ms. The engine installs in minutes on
Ubuntu or BOSS OS via a single script, hooks into bash and zsh, and works with a
one-click optional bubblewrap sandbox for untrusted downloads. By making the
terminal defend itself, csengine brings practical, sovereign, atma-nirbhar AI
safety to every Indian government and enterprise desktop — no cloud, no vendor,
no data leaves the machine.

## 2. Problem Statement

Users routinely execute destructive or risky shell commands with no safeguard.
Human error, social engineering, and copy-paste of malicious snippets from the web
cause irreversible data loss, credential theft, and system compromise. Existing
solutions are either heavy enterprise SIEM products, cloud-dependent AI assistants
that cannot be used on sovereign/government systems, or hard blocklists that annoy
users with false positives and teach them to disable protection.

**We need: a fast, accurate, fully offline safety layer for the shell that catches
dangerous commands in real time, explains why, offers a safe alternative, and
keeps the user in control — without false-positive fatigue.**

## 3. Proposed Solution

| Component | Technology | Role |
|---|---|---|
| Rule Engine | Python + YAML rules | 20 deterministic rule groups, MITRE-mapped, instant |
| ML Classifier | scikit-learn RandomForest | Generalises to novel commands from 20 hand-crafted features |
| LLM Explainer | Ollama + Qwen 2.5 3B Q4 | Human explanations for ambiguous/novel commands |
| Sandbox | bubblewrap (optional) | Safe execution of untrusted downloads |
| Shell Hooks | bash-preexec / zsh preexec | Intercepts every command before execution |
| Audit | SHA-256-hashed JSONL log | Privacy-preserving accountability |

**Decision logic:** a critical rule match always BLOCKs (safety-first, even if the
ML model is unsure — defence in depth). Otherwise rule risk and ML label risk are
blended into a 0-100 score: BLOCK ≥ 80, WARN ≥ 45, else ALLOW. Whitelisted
commands skip analysis entirely (zero false positives for daily workflows).

**Results (measured):**
- ML accuracy **90.9%**; macro F1 **0.904** (destructive 0.881, risky 0.922, safe 0.910)
- Feature extraction + rule check: **0.47 ms** mean (p95 0.64 ms)
- Full pipeline: **56 ms** mean (p95 81 ms) on Windows dev box; faster on Linux
- Regression suite: **22/22 tests passing**
- Dataset: **1,149 commands** (568 safe / 374 risky / 207 destructive), synthetic
  generator covering OWASP + MITRE ATT&CK + GTFOBins patterns

## 4. Innovation / Novelty

1. **Defence-in-depth fusion of rules + ML + LLM** where the LLM is invoked
   *only* on demand (ambiguous or novel commands), keeping latency and power draw
   near zero while still offering natural-language explanations.
2. **Safety-first critical override:** a single critical rule match blocks
   regardless of ML confidence — the model cannot talk the system out of a block.
3. **Fully offline, sovereign-first:** no cloud API, no data egress; aligned with
   India's AtmaNirbhar/sovereign OS mission and deployable on BOSS Linux.
4. **0 ms overhead on the happy path:** whitelist short-circuit means everyday
   commands cost nothing, eliminating the false-positive fatigue that kills other
   tools.
5. **Privacy-preserving audit:** commands are stored only as truncated SHA-256
   hashes, enabling forensics without storing plaintext commands.
6. **Safe-alternative suggestions:** every rule carries a constructive
   "do this instead" so users learn secure habits instead of just being blocked.

## 5. Alignment with C-DAC Mission

- Runs fully offline on **BOSS OS** (India's sovereign GNU/Linux distribution)
- Uses only **open-source models and tools** (Qwen 2.5, scikit-learn, Ollama, bubblewrap)
- No reliance on foreign cloud AI providers; data never leaves the device
- Directly improves the security posture of Indian government and enterprise desktops
- Demonstrable within minutes on the target OS — practical, deployable AI

## 6. Quick Start (demo machine)

```bash
git clone <repo-url> && cd command-safety-engine
bash setup.sh            # venv, deps, model training, Ollama pull, hooks
source ~/.bashrc
csengine status
csengine check "rm -rf /"          # BLOCK
csengine check "chmod -R 777 /var/www"   # WARN
csengine check "git status"        # ALLOW (instant)
```

---

## 7. Demo Video Script (~4 minutes, one take)

> Record with `asciinema` or OBS on a clean Ubuntu/BOSS VM (4 GB RAM, 2 vCPU).
> Background: minimal desktop, terminal maximised.

| # | Scene | What the viewer sees | Narration (15 s) |
|---|---|---|---|
| 1 | **Hook-in-action** | Type `echo hello` → nothing happens (0 overhead) | "The engine watches every command silently." |
| 2 | **Safe whitelist** | Type `git status`, `ls -la`, `cd ~` → ALLOW, sub-ms | "Daily commands pass through instantly — zero false positives." |
| 3 | **Destructive block** | Type `rm -rf /` → BLOCK table: R001, MITRE T1485, "Makes the OS unusable", alternative `rm -rf /path/to/folder`, exit code 2 | "A recursive root deletion is caught and blocked with a safe alternative." |
| 4 | **Fork bomb** | Type `:(){ :|:& };:` → BLOCK, R008, T1498 | "Even a fork bomb is recognised — and critical rules always win." |
| 5 | **Risky warn** | Type `chmod -R 777 /var/www` → WARN, R007, 58/100 | "Riskier commands warn and ask you to confirm." |
| 6 | **ML generalisation** | Type a novel attack not in the rules (e.g. `base64 -d <<< <payload> | bash`) → WARN/BLOCK via ML + rule | "The ML model catches attacks no rule can enumerate." |
| 7 | **LLM explanation** | Type a deliberately ambiguous command with Ollama running → natural-language explanation appears | "For genuinely novel commands, a local Qwen model writes a plain-language explanation — still fully offline." |
| 8 | **Audit** | `cat ~/.csengine/audit.log` → hashed entries | "Every decision is audited, and privacy is preserved — only hashes are stored." |
| 9 | **Status** | `csengine status` → rules loaded, model loaded, LLM available | "The whole system runs on this laptop, on BOSS OS, with nothing sent to the cloud." |

**Video tips:** keep it under 4:30; screen record at 1080p; one terminal window,
no cuts needed; end card with repo URL. The demo_seed_commands.sh script in the
repo automates scenes 2-6.

## 8. Roadmap (post-hackathon)

- BOSS OS `.deb` packaging polish + RPM for other Indian distros
- More languages for explanations (Hindi-first UI)
- Time-based learning: personal allowlists that adapt per user
- Containment: auto-sandbox risky-but-required commands via bubblewrap
- IDE/sudo integration and Docker alias hooking

## 9. Submission Checklist

- [ ] Register on **ssm.cdac.in** before **04 Aug 2026** (team of 1-5)
- [ ] Push repo to GitHub (public)
- [ ] Record demo video per Section 7 (~4 min)
- [ ] Submit final on portal before **25 Aug 2026** (portal also lists idea submission 28 Aug — submit early)
- [ ] Keep solution fully offline and open-source (no cloud AI in the demo)
