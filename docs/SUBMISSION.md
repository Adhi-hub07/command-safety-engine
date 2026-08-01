# Command Safety Engine — C-DAC Secure OS Hackathon 2026 Submission

**Track:** AI @ Application Level (sub-problem: Command Safety)
**Target OS:** Ubuntu 22.04/24.04, BOSS Linux
**Status:** code complete — all 28 tests passing, model trained, demo-ready

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
explanations and safe alternatives. **Layer 2** is a GradientBoosting machine-learning
classifier trained on 1,379 deduplicated synthetic/real-world shell commands
(83.3% accuracy on a held-out test, 0.80 macro F1, 0.83 destructive-class recall)
that generalises to novel commands no rule covers. **Layer 3** is a
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
| ML Classifier | scikit-learn GradientBoosting | Generalises to novel commands from 20 hand-crafted features |
| LLM Explainer | Ollama + Qwen 2.5 3B Q4 | Human explanations for ambiguous/novel commands |
| Sandbox | bubblewrap (optional) | Safe execution of untrusted downloads |
| Shell Hooks | bash-preexec / zsh preexec | Intercepts every command before execution |
| Audit | SHA-256-hashed JSONL log | Privacy-preserving accountability |

**Decision logic:** a critical rule match always BLOCKs (safety-first, even if the
ML model is unsure — defence in depth). Otherwise rule risk and ML label risk are
blended into a 0-100 score: BLOCK ≥ 80, WARN ≥ 45, else ALLOW. Whitelisted
commands skip analysis entirely (zero false positives for daily workflows).

**Results (measured, honest = deduplicated + 5-fold CV):**
- Deployed model (GradientBoosting): **5-fold CV 0.834 ± 0.031 acc, 0.807 ± 0.040 macro-F1**
- Held-out test (80/20, seed 42): **83.3% accuracy, 0.803 macro-F1**
  (per-class recall: destructive **0.833**, risky 0.605, safe 0.947)
- Feature extraction + rule check: **0.47 ms** mean (p95 0.64 ms)
- Full pipeline: **56 ms** mean (p95 81 ms) on Windows dev box; faster on Linux
- Regression suite: **28/28 tests passing**, ruff lint clean
- Dataset: **1,379 unique commands** (759 safe / 381 risky / 239 destructive) built by a
  deterministic three-step pipeline — `generate_synthetic.py` → `auto_label_raw.py`
  (300 real-world commands) → `dedupe_dataset.py` — with per-row provenance
  (`bash-history` 358, `mitre-attack` 234, `gtfobins` 19, `synthetic` 768)
- **Data-hygiene audit:** 666 duplicate rows were removed after the first regeneration
  (they leaked identical commands into both train and test, inflating accuracy from an
  honest ~80% CV to a misleading ~92%); the pipeline now removes duplicates at build time
- **Model comparison** (identical 80/20 split, seed 42, run via `src/ml/compare.py`):

  | Model | Accuracy | Macro-F1 | Destructive recall | Risky recall | Safe recall |
  |---|---|---|---|---|---|
  | **GradientBoosting (deployed)** | **0.833** | **0.803** | **0.833** | 0.605 | 0.947 |
  | RandomForest | 0.819 | 0.792 | 0.771 | 0.658 | 0.915 |
  | LogisticRegression | 0.822 | 0.789 | 0.729 | 0.645 | 0.941 |

  GradientBoosting is deployed because on the deduplicated dataset it wins on **both**
  macro-F1 (0.803) and destructive-class recall (0.833) — for a blocker, missing a
  destructive command is the worst failure mode, and this is also the highest destructive
  recall of the three models. (An earlier dataset carried duplicate rows that changed the
  ranking; removing them made the comparison trustworthy.)

### Data provenance (reproducibility)

The dataset is rebuilt deterministically (seed 42) by a three-step pipeline:
`data/synthetic/generate_synthetic.py` → `scripts/auto_label_raw.py` (labels the
300-row raw corpus `data/raw/commands_raw.csv`) → `scripts/dedupe_dataset.py`
(removes duplicate commands and resolves label conflicts toward the most severe
class). Every row in `data/labeled/commands_labeled.csv` carries a `source` column:
- **bash-history** — everyday benign commands sampled from real shell histories
  (safe + risky patterns like repeated `rm -rf` on project dirs).
- **mitre-attack** — adversarial commands derived from MITRE ATT&CK techniques
  (T1485 data destruction, T1498 network DoS, T1059 command-and-scripting,
  T1219 RAT deployment, T1027 obfuscated payloads, T1552 credential extraction).
- **gtfobins** — living-off-the-land Linux binaries from GTFOBins (tar checkpoint
  execution, vim `-c`, awk/find -exec, gdb, perl) used as destructive/risky samples.
- **synthetic** — programmatically generated rule-adjacent variants (staging,
  permissions, obfuscation, download-and-run) from `data/synthetic/generate_synthetic.py`
  (seed 42 → identical regeneration every run).

**False-positive hardening:** the rule regexes are anchored and escaped — the
regression suite proves `rm -rf build/`, `rm -rf vendor/`-style commands are WARN,
never BLOCK (naive substring detectors fail exactly here).

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

## 10. Judge Preparation — Anticipated Q&A

**Q: How do you handle false positives — the classic complaint against safety tools?**
A: Three layers of defence. (1) A **whitelist of daily commands** short-circuits analysis
— `git status`, `ls`, `cd` cost 0 ms and are never flagged. (2) Rules are **anchored and
escaped**, not naive substrings: `rm -rf build/` is WARN while `rm -rf /*` is BLOCK —
proven by regression tests. (3) The output is **graded** (ALLOW / WARN / BLOCK), so risky
work is confirmed, not prohibited; WARN is the signal, not the verdict.

**Q: Why not a deep-learning model instead of GradientBoosting?**
A: A shallow GradientBoosting classifier on 20 hand-crafted features is deliberate. It
trains on CPU in ~1 s, runs in ~0.1 ms, needs no GPU, and is fully explainable — judges and
auditors can read exactly which features fired (e.g. `targets_root_fs`). We measured deep
models offer no accuracy gain at this data scale, and they make the sovereign/offline story
(runs on any office PC, BOSS OS) harder to sell.

**Q: How does the model generalise beyond its training set?**
A: The feature space encodes *intent*, not syntax: flags, targets, redirections,
obfuscation, sudo usage. A novel attack (say a new download-and-run trick) still trips
`has_redirect` + `network_recon` + `is_pipe_to_shell` features even if the exact string was
never seen. The comparison script proves the 3-class split (safe/risky/destructive)
generalises to a held-out 20% with destructive recall 0.833, and 5-fold CV reports 0.834 ±
0.031 accuracy (no single-split cherry-picking).

**Q: What happens if the LLM is unavailable (no Ollama, no network)?**
A: The LLM is optional by design. A 0.5 s TCP probe checks Ollama; on failure the engine
returns the rule/ML explanation instantly. Nothing waits on a network call — the safety
decision never depends on a model that may not be there.

**Q: How is user privacy preserved?**
A: Commands are never stored in plaintext. The audit log keeps only the first 8 chars of
the SHA-256 of the command plus the verdict — enough to correlate incidents, impossible to
reverse into the command. No data ever leaves the device.

**Q: What if a user legitimately needs to run a dangerous command?**
A: The user is in control. A WARN asks for confirmation; a BLOCK can be overridden with an
explicit `csengine allow` decision recorded in the audit log. Safety layers that cannot be
overridden are bypassed and abandoned — ours keeps the final say with the human, always.

**Q: What about legitimate-but-risky workflows (e.g. `mkfs` on a known disk)?**
A: The 3-class design handles this: `mkfs.ext4 /dev/sda` is WARN/BLOCK with a
context-aware explanation and a safe alternative (`mkfs.ext4 -L volume /dev/sdb` with the
disk checked first). Whitelists can mark trusted operations. The graded design reduces
annoyance to exactly the risk level, not the tool.

**Q: How is the rule set kept current?**
A: Rules live in `config/rules.yaml` — version-controlled, reviewable, hot-reloadable
(no retraining needed for rule changes). CI runs lint + train + pytest on every push so a
rule edit can never ship broken. Data sources (MITRE ATT&CK, GTFOBins) are cited per-row
in the dataset for traceability.

**Q: What is the measured performance?**
A: Feature+rule: 0.47 ms mean (p95 0.64 ms). Full pipeline with ML: ~56 ms mean. Whitelist
happy path: effectively 0. On the demo machine the overhead is invisible to typing.

**Q: Why is this better than existing OS safeguards (sudo, SELinux, chroot)?**
A: Those tools prevent *unauthorised* actions or isolate workloads; none interpret the
*user's typed intent* in real time. csengine sits between keyboard and kernel, understands
command semantics (including obfuscated, multi-stage, or downloaded payloads), explains in
plain language, and offers constructive alternatives — complementing SELinux/sudo rather
than replacing them.

**Q: Can you demo something it catches that blocklists cannot?**
A: Yes — scene 6 of the demo: a base64-obfuscated download-and-run payload that no
blocklist string can match is flagged by the ML layer (obfuscation + network + pipe
features), and an LLM explanation appears in plain language, fully offline.

## 11. Submission Checklist

- [ ] Register on **ssm.cdac.in** before **04 Aug 2026** (team of 1-5)
- [ ] Push repo to GitHub (public)
- [ ] Record demo video per Section 7 (~4 min)
- [ ] Submit final on portal before **25 Aug 2026** (portal also lists idea submission 28 Aug — submit early)
- [ ] Keep solution fully offline and open-source (no cloud AI in the demo)
