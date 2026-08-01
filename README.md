<p align="center">
  <img src="assets/tux.png" alt="Linux logo" width="120" />
  <br />
  <strong style="font-size: 34px;">COMMAND SAFETY ENGINE</strong>
  <br />
  <em>Offline AI guard for the Linux shell</em>
</p>

> **Made by Adhithya J** · C-DAC Secure OS Hackathon 2026 · Track 1 (AI @ Application Level)

> 🌐 **Live website:** <https://adhi-hub07.github.io/command-safety-engine/>

Every command you type is checked **before it runs**. Dangerous commands are
**blocked**, risky ones ask for **confirmation**, and everything else passes
through in milliseconds — fully offline, fully open-source, on a normal laptop.

```
Command → Rule Engine → ML Classifier → Local LLM (Qwen 2.5 3B) → Allow / Warn / Block
```

---

## Table of Contents

- [What it does](#what-it-does)
- [Features](#features)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Installation](#installation)
  - [One-shot installer (`setup.sh`)](#one-shot-installer)
  - [BOSS OS](#boss-os)
  - [Manual install](#manual-install)
- [Usage](#usage)
  - [CLI reference](#cli-reference)
  - [Exit codes](#exit-codes)
  - [Shell hooks](#shell-hooks)
- [Performance & ML honesty](#performance--ml-honesty)
- [Dataset provenance](#dataset-provenance)
- [Project layout](#project-layout)
- [Documentation](#documentation)
- [Demo](#demo)
- [Roadmap](#roadmap)
- [License](#license)

---

## What it does

A terminal is the most powerful interface on a Linux machine — and the least
protected. One mistyped or copy-pasted command (`rm -rf /`, a fork bomb, a
`curl | bash` chain) can destroy data or hand an attacker the machine. No
mainstream OS ships a safety layer between the keyboard and the kernel.

**csengine** is that layer. It sits inside your shell (bash **and** zsh),
inspects every command you type, and decides in real time:

| Verdict | Meaning | Exit code |
|---|---|---|
| **ALLOW** | Safe, whitelisted, or low risk — runs instantly | `0` |
| **WARN** | Risky — ask the user to confirm before running | `1` |
| **BLOCK** | Destructive — refuse to run, explain why, suggest a safe alternative | `2` |

Every decision is explained in plain English, mapped to MITRE ATT&CK, and
recorded in a privacy-preserving audit log (hashes only — never plaintext).

## Features

- **100% offline** — no cloud APIs, no telemetry, no data egress. Aligned with
  India's sovereign OS (AtmaNirbhar) mission and fully functional on air-gapped
  networks.
- **Hybrid AI, three layers of defence-in-depth**
  1. **Rule engine** — 20 deterministic MITRE-mapped rule groups (R001–R020)
  2. **ML classifier** — scikit-learn GradientBoosting, trained on 1,379 real
     + synthetic commands, 3 classes (safe / risky / destructive)
  3. **Local LLM** — Qwen 2.5 3B via Ollama, invoked *only* for ambiguous or
     novel commands to write natural-language explanations
- **Fast** — rules + ML path ≈ 0.34 ms mean (p95 0.61 ms); full pipeline ≈ 3 ms.
  Whitelisted daily commands cost ~0 ms.
- **Safety-first override** — a single critical rule match blocks regardless of
  ML confidence. The model can never talk the system out of a block.
- **Explains & teaches** — every warning shows the matched rule, its MITRE
  mapping, why it matters, and a safer rewrite (`rm -rf /path/to/folder`).
- **Privacy-preserving audit** — `~/.csengine/audit.log` stores only truncated
  SHA-256 hashes of commands, so incidents are forensically correlatable but
  commands can never be recovered.
- **Works on BOSS OS** (Indian government GNU/Linux) and standard
  Ubuntu / Debian, and on both **bash and zsh**.
- **Optional bubblewrap sandbox** — dry-run untrusted downloads safely.
- **Honest ML numbers** — 5-fold cross-validation, deduplicated data, no
  cherry-picked single splits (see [Performance](#performance--ml-honesty)).

## How it works

```
                    ┌──────────────────────────────────────────────────────┐
  user types cmd    │              Command Safety Engine                  │
 ────────────────►  │                                                      │
                    │  1. Preprocess                                       │
                    │     normalize · alias expansion · $VAR resolution    │
                    │        │                                             │
                    │        ▼                                             │
                    │  2. Tokenize (bashlex / fallback)                    │
                    │     words · pipes · redirects · substitutions        │
                    │        │                                             │
                    │        ▼                                             │
                    │  3. Rule Engine (rules.yaml, 20 rule groups)         │
                    │     fast deterministic match  ──┐                    │
                    │        │                        │ severity+MITRE    │
                    │        ▼                        ▼                   │
                    │  4. Feature Extraction (20 features)                 │
                    │        │                                             │
                    │        ▼                                             │
                    │  5. ML Classifier (GradientBoosting, 3 classes)      │
                    │     safe / risky / destructive                       │
                    │        │                                             │
                    │        ▼                                             │
                    │  6. LLM (Qwen 2.5 3B via Ollama, offline)            │
                    │     plain-English explanation + safer alternative     │
                    │     (only for ambiguous / flagged commands)          │
                    │        │                                             │
                    │        ▼                                             │
                    │  7. Decision fusion                                  │
                    │     risk_score 0-100 → ALLOW / WARN / BLOCK          │
                    │        │                                             │
                    │        ▼                                             │
                    │  8. Output (rich CLI / JSON) + audit log             │
                    └──────────────┬───────────────────────────────────────┘
                                   ▼
                         shell hook (bash/zsh preexec)
```

### Decision fusion

```
rule_score = max severity of matched rules (0-100)
ml_risk    = label_risk × ml_confidence
risk_score = rule_score×(1-w) + ml_risk×w,  w=0.35 if confident else 0.15

critical rule AND ML=destructive  → BLOCK
risk_score ≥ 80                   → BLOCK
risk_score ≥ 45                   → WARN
else                              → ALLOW
```

## Quick start

See it live first: **<https://adhi-hub07.github.io/command-safety-engine/>** (interactive demo terminal)

```bash
git clone <repo-url>
cd command-safety-engine
bash setup.sh          # venv + deps + model training + Ollama + shell hooks
source ~/.bashrc
```

Then try it:

```bash
csengine status                      # rules, model, LLM availability
csengine check "rm -rf /"            # BLOCK (exit 2)
csengine check "chmod -R 777 /var/www"  # WARN (exit 1)
csengine check "git status"          # ALLOW (exit 0, instant)
```

## Installation

### Step-by-step setup on Linux (Ubuntu / Debian / BOSS OS)

**1. Install prerequisites**

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip curl
```

(optional, for LLM explanations — works without it, rule+ML path only):

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b-instruct-q4_K_M
```

**2. Clone and install**

```bash
git clone <repo-url>
cd command-safety-engine
bash setup.sh          # venv + deps + model training + Ollama + shell hooks
source ~/.bashrc
```

**3. Verify it works**

```bash
csengine status                      # rules, model, LLM availability
csengine check "rm -rf /"            # BLOCK (exit 2) — dangerous command refused
csengine check "chmod -R 777 /var/www"  # WARN (exit 1) — confirm before running
csengine check "git status"          # ALLOW (exit 0) — instant, zero false positive
```

That's it — the hook is now active in every new terminal: dangerous commands
are blocked before they run, risky ones need a confirming Enter, everything
else is untouched.

### One-shot installer

`setup.sh` does everything: creates an isolated venv, installs dependencies,
generates the labeled dataset, trains the ML classifier, pulls the local Qwen
model (if Ollama is present), installs the shell hook, and puts the
`csengine` command on your PATH.

```bash
bash setup.sh
```

> The hook and the `csengine` command are active in **new terminals**
> (`~/.csengine/bin` is added to PATH in `~/.bashrc`). To activate now:
> `source ~/.bashrc`

### BOSS OS

```bash
bash install-boss-os.sh                 # quick path
# or build a .deb:
CSENGINE_BUILD_DEB=1 bash install-boss-os.sh
sudo dpkg -i ~/.csengine/deb/command-safety-engine_1.0_amd64.deb
```

Verify offline operation (core demo point — government systems often run on
restricted networks):

```bash
nmcli radio all off          # or: sudo ip link set <iface> down
csengine status              # LLM available, all layers loaded
csengine check "rm -rf /"    # BLOCK — works with zero network
nmcli radio all on
```

### Manual install

```bash
python3 -m venv ~/.csengine/venv
~/.csengine/venv/bin/pip install -r requirements.txt
# train the ML model
~/.csengine/venv/bin/python -m src.ml.train
# install the shell hook
~/.csengine/venv/bin/python src/main.py install-hook bash   # or zsh
# optional LLM
ollama pull qwen2.5:3b-instruct-q4_K_M
```

Requirements: Python 3.8+, ~1 GB RAM (3 GB if the LLM is used), any
Ubuntu/Debian/BOSS OS machine.

## Usage

### CLI reference

```
csengine check "<command>"              analyze one command
csengine check --json "<command>"       analyze, print JSON
csengine check --audit "<command>"      analyze and write to the audit log
csengine install-hook [bash|zsh]        install the shell preexec hook
csengine status                         show model / LLM availability
csengine --version
```

### Exit codes

Hooks (and your own scripts) use exit codes as verdicts:

| Exit | Verdict | Hook behaviour |
|---|---|---|
| `0` | ALLOW | command runs |
| `1` | WARN | hook asks you to type the command again to confirm |
| `2` | BLOCK | hook refuses — command never executes |

Example in a script:

```bash
csengine check "$cmd" --json >/dev/null
case $? in
  0) echo "safe to run" ;;
  1) echo "risky — ask for confirmation" ;;
  2) echo "blocked" ;;
esac
```

### Shell hooks

The hooks intercept **every command** typed interactively:

- **bash** — via bash-preexec (`hooks/bash-preexec.sh`) with the DEBUG-trap
  path (`shopt -s extdebug`), which lets a non-zero preexec return actually
  block the command.
- **zsh** — via a custom `accept-line` widget on the Enter key, so `BLOCK`
  clears the line before anything can run; `WARN` keeps the line and waits for
  a confirming Enter.

**Retyping to confirm:** a `WARN` command is blocked on the first Enter; type
the exact same command again to run it. A `BLOCK` can only be bypassed
explicitly.

```bash
export CSENGINE_DISABLE=1    # kill-switch: temporarily disable the hook
unset CSENGINE_DISABLE       # re-enable
```

The Linux build is verified end-to-end with a real-PTY test that drives an
interactive shell and proves a destructive `dd` command never executes and a
risky `chmod` requires confirmation:

```bash
python3 scripts/test_hook_pty.py     # bash + zsh, ALL PASS
bash scripts/verify_demo.sh          # 17/17 checks: CLI, hooks, audit, benchmark
```

## Performance & ML honesty

Measured on the dev box via `scripts/benchmark_latency.py --n 1000`
(regenerated in CI on every push):

| Path | Mean | p95 |
|---|---|---|
| Feature extraction + rule check | ~0.34 ms | ~0.61 ms |
| Full pipeline (no LLM resident) | ~3 ms | ~3.5 ms |
| Whitelisted daily command | ~0 ms | ~0 ms |
| With local Qwen pre-warmed | tens of ms | — |

**Model quality** — honest numbers on *deduplicated* data with 5-fold
cross-validation (no cherry-picked single split):

- 5-fold CV: **0.834 ± 0.031 accuracy**, **0.807 ± 0.040 macro-F1**
- Held-out test (80/20, seed 42): **83.3% accuracy**, 0.803 macro-F1
- Per-class recall (held-out): destructive **0.833**, risky 0.605, safe 0.947

Model comparison on the identical split (`src/ml/compare.py`):

| Model | Accuracy | Macro-F1 | Destructive recall |
|---|---|---|---|
| **GradientBoosting (deployed)** | **0.833** | **0.803** | **0.833** |
| RandomForest | 0.819 | 0.792 | 0.771 |
| LogisticRegression | 0.822 | 0.789 | 0.729 |

> GradientBoosting is deployed because it wins on both macro-F1 *and* the
> destructive-class recall — for a blocker, missing a destructive command is
> the worst failure mode.

**Data-hygiene note:** an early regeneration carried 666 duplicate rows that
leaked identical commands into both train and test (inflating the number to a
misleading ~92%). The pipeline now deduplicates at build time — these are the
honest ~83% numbers.

## Dataset provenance

The dataset (`data/labeled/commands_labeled.csv`, **1,379 unique commands**:
759 safe / 381 risky / 239 destructive) is rebuilt deterministically (seed 42)
by a three-step pipeline:

```
data/synthetic/generate_synthetic.py   →   scripts/auto_label_raw.py   →   scripts/dedupe_dataset.py
```

Every row carries a `source` column for traceability:

| Source | Origin |
|---|---|
| `synthetic` (768) | programmatic rule-adjacent variants, seeded |
| `bash-history` (358) | everyday benign commands from real shell histories |
| `mitre-attack` (234) | adversarial commands from MITRE ATT&CK techniques |
| `gtfobins` (19) | living-off-the-land Linux binaries |

**False-positive hardening:** rule regexes are anchored and escaped — the
regression suite proves `rm -rf build/` is **WARN**, never BLOCK, while
`rm -rf /*` is BLOCK.

## Project layout

```
command-safety-engine/
├── config/            # rules.yaml (20 rule groups), whitelist.yaml, config.yaml
├── data/
│   ├── raw/           # real-world command corpus (300 rows)
│   ├── labeled/       # deduplicated labeled dataset (1,379 rows)
│   └── synthetic/     # seeded command generator
├── notebooks/         # model experiments (5-fold CV comparison) — dev only
├── src/
│   ├── parser/        # bashlex-based command tokenizer
│   ├── features/      # 20-feature extractor
│   ├── rules/         # deterministic rule engine (R001–R020)
│   ├── ml/            # training, evaluation, comparison
│   ├── llm/           # local Ollama explanation layer (Qwen 2.5 3B)
│   ├── sandbox/       # optional bubblewrap dry-run
│   ├── output/        # JSON + rich CLI formatting
│   ├── engine.py      # orchestrator + decision fusion + audit
│   └── main.py        # CLI entrypoint
├── hooks/
│   ├── csengine.bash  # bash preexec hook
│   ├── csengine.zsh   # zsh accept-line widget hook
│   └── bash-preexec.sh
├── scripts/
│   ├── verify_demo.sh      # Linux smoke test (17/17 checks)
│   ├── test_hook_pty.py    # real-PTY interactive hook test (bash + zsh)
│   ├── benchmark_latency.py
│   ├── label_data.py / auto_label_raw.py / dedupe_dataset.py
│   └── demo_seed_commands.sh
├── tests/             # pytest regression suite (31 tests)
├── docs/              # architecture, features, BOSS OS, submission
├── setup.sh           # one-shot installer
└── install-boss-os.sh # BOSS OS / .deb installer
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — data flow, design principles, decision fusion
- [Feature dictionary](docs/FEATURES.md) — all 20 ML features with examples
- [BOSS OS integration](docs/BOSS_OS_INTEGRATION.md) — install, offline verification, .deb packaging
- [Submission](docs/SUBMISSION.md) — abstract, demo script, Q&A prep for judges

## Demo

A ~4-minute demo script is in [docs/SUBMISSION.md §7](docs/SUBMISSION.md#7-demo-video-script-4-minutes-one-take)
with `scripts/demo_seed_commands.sh` automating the scenes: block a fork bomb,
warn on `chmod -R 777`, catch a novel base64-obfuscated attack with ML, show
the hashed audit log, and prove everything works with the network switched off.

## Roadmap

- BOSS OS `.deb` polish + RPM for other Indian distributions
- Hindi-first explanations for the LLM layer
- Personal time-based allowlists that adapt per user
- Auto-sandbox of risky-but-required commands via bubblewrap
- IDE / sudo integration and Docker alias hooking

## License

[MIT](LICENSE) © 2026 Adhithya J
