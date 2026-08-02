# Portal Submission — Copy-Paste Fields

Stage-1 solution submission portal: **ssm.cdac.in**.
Compulsory fields below. Copy each block verbatim into the matching form field.
`docs/architecture.png` is the architecture image (field 6).

---

## 1. Project Title

**Command Safety Engine (csengine) — an offline AI guard for the Linux shell**

---

## 2. Objective

Build a fast, accurate, fully offline command-analysis layer that intercepts every
shell command before execution, classifies it as safe / risky / destructive,
explains the decision in plain language, recommends a safer alternative, and asks
for confirmation before anything harmful reaches the operating system — while
keeping the user in control and preserving system security. Everything runs
on-device (no cloud, no telemetry) so it is deployable on sovereign and
air-gapped systems such as BOSS OS.

---

## 3. Problem Statement Addressed

*Quoted verbatim from the hackathon problem statement:*

> Design an intelligent command analysis layer that evaluates Linux commands
> before execution, understands user intent, identifies potential risks, and
> recommends safer alternatives while preserving user control and system
> security.

Our system is a direct, deployable answer to Problem Statement 3.

---

## 4. Novelty

1. **Defence-in-depth fusion of rules + ML + LLM** where the LLM is invoked only
   on demand (ambiguous or novel commands), keeping idle latency and power draw
   near zero while still producing natural-language explanations.
2. **Safety-first critical override:** a single critical rule match blocks the
   command regardless of ML confidence — the model can never talk the system out
   of a block.
3. **Fully offline, sovereign-first:** no cloud API, no data egress; aligned with
   India's AtmaNirbhar / sovereign-OS mission; runs on BOSS OS.
4. **Zero overhead on the happy path:** a whitelist short-circuit means everyday
   commands cost ~0 ms and are never flagged, eliminating the false-positive
   fatigue that makes other safety tools get disabled.
5. **Privacy-preserving audit:** commands are stored only as truncated SHA-256
   hashes, enabling forensics without storing plaintext commands.
6. **Safe-alternative suggestions on every rule:** the tool teaches secure habits
   instead of just refusing.

---

## 5. Detailed Description

**Command Safety Engine (csengine)** sits between the keyboard and the kernel. A
bash/zsh preexec hook forwards every typed command to a three-layer pipeline:

- **Layer 1 — Rule engine:** 27 MITRE ATT&CK-aligned deterministic rule groups
  (R001–R027) covering recursive root deletion, fork bombs, permission
  escalation, credential scraping, download-and-run supply chains, system-file
  tampering, raw block-device writes, obfuscation and more. Each rule carries a
  severity, a MITRE technique mapping, a human-readable reason and a safe
  alternative. Rules run in < 0.5 ms.
- **Layer 2 — ML classifier:** a scikit-learn GradientBoosting model over 20
  hand-crafted *intent* features (flags, targets, redirections, pipes,
  obfuscation, network calls, disk ops, sudo, wildcards…). It classifies
  commands as safe / risky / destructive in ~0.1 ms and catches novel attacks no
  rule enumerates.
- **Layer 3 — LLM explainer:** Qwen 2.5 3B (open-source) served via Ollama, fully
  offline. Invoked only for ambiguous or flagged commands to write a plain-language
  explanation and safer alternative. A 0.5 s TCP probe makes it gracefully optional —
  safety never waits on the LLM.

The three layers are fused into a 0–100 risk score: BLOCK ≥ 80 (or any critical
rule), WARN 45–79 (asks to confirm), else ALLOW. Whitelisted commands skip
analysis entirely. Every decision is written to a SHA-256-hashed offline JSONL
audit log. An optional bubblewrap sandbox can dry-run untrusted downloads.

Measured performance (Kali VM, `scripts/benchmark_latency.py`): whitelist path
~0 ms; feature+rule ~0.3 ms mean (p95 ~0.5 ms); full pipeline ~2.7 ms mean with
no LLM resident.

---

## 6. Architecture Image

`docs/architecture.png` (1600×900, attached to this submission). Repo path:
`docs/architecture.svg` (editable source).

---

## 7. Technical Description (open-source / in-house disclosure)

100% open-source; no proprietary or cloud components. All software is disclosed:

- **Languages/tooling:** Python 3.10+ (ruff-linted), bash/zsh hooks
- **Rule engine:** in-house, `config/rules.yaml` (27 groups) + `src/rules/`
- **ML:** scikit-learn GradientBoosting (in-house feature engineering,
  `src/features/`), trained in-repo via CI on the committed dataset
- **LLM:** Qwen 2.5 3B `qwen2.5:3b-instruct-q4_K_M` via Ollama (both open-source)
- **Tokenization:** bashlex with a built-in fallback for malformed input
- **Sandbox:** bubblewrap (optional)
- **Audit:** Python stdlib JSONL, SHA-256 hashing

No external AI APIs are called; the demo runs with no network access.

---

## 8. GitHub Repository Link

https://github.com/Adhi-hub07/command-safety-engine

(Private per Section 7.2.1; official account `ssm-hackathon` added as
collaborator. Includes README, LICENSE (MIT), complete buildable source,
CI workflow, tests, and all project resources.)

---

## 9. Dataset Description

- **`data/labeled/commands_labeled.csv` — 1,379 unique rows**
  (759 safe / 381 risky / 239 destructive), with per-row provenance.
- Built by a deterministic three-step pipeline (seed 42):
  `data/synthetic/generate_synthetic.py` → `scripts/auto_label_raw.py`
  → `scripts/dedupe_dataset.py`.
- Sources: **bash-history** 358 (everyday benign + risky real-world commands),
  **mitre-attack** 234 (commands derived from MITRE ATT&CK techniques:
  T1485 data destruction, T1498 DoS, T1059 command-and-scripting, T1219 RAT,
  T1027 obfuscation, T1552 credential extraction), **gtfobins** 19
  (living-off-the-land binaries: tar checkpoint, vim -c, awk/find -exec, gdb,
  perl), **synthetic** 768 (rule-adjacent programmatic variants).
- **Data hygiene:** 666 duplicate rows were removed at build time — duplicates
  had leaked identical commands into both train and test, inflating accuracy to a
  misleading ~92%. The honest, deduplicated figure is ~81% CV / 82.2% held-out.
- Raw corpus: `data/raw/` (bash_history 358, mitre-attack 234, gtfobins 19,
  synthetic scripts) — 768 non-labelled rows total.

---

## 10. Evaluation Methodology

- **Split:** 80/20 stratified train/held-out, seed 42, plus 5-fold cross-validation
  (no single-split cherry-picking).
- **Metrics:** accuracy, macro F1, and per-class recall (destructive is the class
  that must not be missed).
- **Model comparison:** GradientBoosting vs RandomForest vs LogisticRegression on
  the identical split (`src/ml/compare.py`).
- **Runtime:** mean/p95 latency via `scripts/benchmark_latency.py --n 1000`.
- **Functional:** 44 pytest regression tests (rules, features, end-to-end,
  wrapper-unwrap, safe battery), `scripts/verify_demo.sh` (17 checks),
  real-PTY hook tests on bash + zsh (pass on Ubuntu and Kali).
- **Reproducibility:** CI (`train.yml`) regenerates the dataset, retrains, and
  runs the full test suite on every push.

---

## 11. Results

- Deployed model (GradientBoosting): **5-fold CV 0.811 ± 0.033 accuracy,
  0.771 ± 0.048 macro-F1**
- Held-out test (80/20, seed 42): **82.2% accuracy, 0.791 macro-F1**
  — per-class recall: destructive **0.771**, risky 0.632, safe 0.934
- Model comparison (identical split): GB 0.822/0.791 · RF 0.794/0.772 ·
  LR 0.815/0.777 (accuracy / macro-F1) — GB deployed (wins macro-F1,
  competitive destructive recall, and the rule engine hard-blocks destructive
  patterns deterministically).
- Latency: feature+rule ~0.3 ms mean (p95 ~0.5 ms); full pipeline ~2.7 ms mean.
- Coverage: 27 rule groups, 87-pattern whitelist; `verify_demo.sh` 17/17;
  44/44 tests; bash+zsh PTY hooks verified on Ubuntu and Kali Linux.
- Rule-verified hard blocks: `rm -rf /`, fork bomb, `dd of=/dev/sda`,
  `mkfs.ext4 /dev/sda`, `shutdown -h now`, `rm --no-preserve-root` and more.

---

## 12. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Adversarial bypass via encoded/obfuscated payloads | Medium | High | Feature extractor decodes base64/hex; obfuscation/redirect/pipe features feed ML; every decision audit-logged; rule layer hard-blocks decoded critical targets |
| 2 | LLM unavailable at demo (no Ollama / no network) | Medium | Medium | LLM is optional by design; 0.5 s TCP probe; rule+ML path answers in < 60 ms; `csengine status` surfaces availability up front |
| 3 | False positives on legitimate workflows | Medium | Medium | 87-pattern whitelist short-circuit; anchored/escaped rules (`rm -rf build/` is WARN, not BLOCK — proven by tests); graded WARN is confirmable, not a hard block |
| 4 | Model drift / silent performance loss | Low | Medium | CI regenerates data, retrains, prints 5-fold CV on every push; dataset rebuild is deterministic (seed 42) |
| 5 | User override abused to disable safety | Low | High | Overrides recorded as SHA-256 hashes; repeat overrides of BLOCK verdicts detectable in the audit log |
| 6 | Privacy leak of typed commands | Low | High | Only truncated SHA-256 hashes stored; fully offline, no network egress by design |

---

## 13. AI Ethics

- **No data exfiltration:** the system is fully offline; no command text or
  telemetry is transmitted anywhere.
- **Privacy by design:** the audit log stores only truncated SHA-256 hashes of
  commands — forensics without plaintext collection.
- **Human-in-the-loop:** the tool never executes anything on its own; it grades
  (ALLOW/WARN/BLOCK) and the user decides. BLOCK can be overridden consciously,
  and the override is logged.
- **Transparency / explainability:** every decision shows the matched rule IDs,
  MITRE technique, ML confidence and a plain-language reason; the ML model is a
  shallow, auditable classifier whose features can be read directly — no opaque
  deep model.
- **Open and reproducible:** open-source, deterministic dataset pipeline, CI on
  every push, honest (deduplicated) metrics — no inflated claims.
- **Purpose and misuse:** designed to *prevent* damage (data loss, DoS,
  credential theft), not to cause it; it reduces risk on real machines.
