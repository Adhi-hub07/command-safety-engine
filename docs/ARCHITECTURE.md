# Architecture

## Data flow

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
                    │  3. Rule Engine (rules.yaml, 27 rule groups)         │
                    │     fast deterministic match  ──┐                    │
                    │        │                        │ severity+MITRE    │
                    │        ▼                        ▼                   │
                    │  4. Feature Extraction (20 features)                 │
                    │        │                                             │
                    │        ▼                                             │
                    │  5. ML Classifier (GradientBoosting, 3 classes)          │
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

## Design principles

1. **Defense in depth** — no single layer is trusted. Rules catch known
   patterns, ML catches novel combinations, LLM explains and handles
   ambiguity. Any layer can override toward *more* caution.
2. **Latency budget** — the rules + ML path runs in <50 ms, so the shell
   hook never feels laggy. The LLM (0.5–3 s) is invoked only when the
   command is ambiguous or already flagged.
3. **Offline by default** — everything runs on-device. No cloud calls, no
   telemetry. Audit logs store only command hashes (opt-in for full text).
4. **Explainability** — every decision shows matched rule IDs, MITRE
   ATT&CK mapping, ML confidence, and a plain-English reason, so users and
   administrators can trust (and audit) the tool.
5. **Graded control** — `ALLOW` / `WARN` / `BLOCK` with an override path.
   Destructive commands require typed confirmation, not a blind yes/no.

## Decision fusion

```
rule_score = max severity of matched rules (0-100)
ml_risk    = label_risk × ml_confidence
risk_score = rule_score×(1-w) + ml_risk×w,  w=0.35 if confident else 0.15

critical rule AND ML=destructive  → BLOCK
risk_score ≥ 80                  → BLOCK
risk_score ≥ 45                  → WARN
else                             → ALLOW
```

## SafeShell layers (transactional execution)

Runs only for non-ALLOW commands, after the verdict:

1. **Path extraction** (`src/transaction/paths.py`) — walks the parsed AST for
   `rm` / `mv` / `cp` / `chmod` / `chown` / `truncate` / `dd` / `touch` / `tee`
   arguments and redirection targets; de-duplicates, expands `~`, filters globs
   and `$VAR`s.
2. **Undo plan** (`src/transaction/plan.py`) — deterministic offline steps
   (`restore`, `move_back`, `chmod_back`, `chown_back`) merged with LLM recovery
   steps when Ollama answers; static steps stay authoritative.
3. **Transaction** (`src/transaction/tx.py`) — snapshots every target with
   `(content, mode, uid, gid, symlink)` into `~/.csengine/tx/<id>/snapshot/`
   (12-hex id, sha256-tagged tree); `undo` replays it byte-for-byte; commit
   discards it.
4. **Simulation** (`src/simulation/run.py`) — copies target parents into a
   staging area (capped at 200 files / 20 MB), runs the command in a
   `bwrap --ro-bind / / --dev /dev --proc /proc --unshare-net --die-with-parent`
   sandbox with staged parents bind-mounted, and diffs the tree (sha256 content
   hashes) into `deleted / modified / created`.

The bash/zsh hooks open a transaction automatically when a WARN command is
re-typed to confirm (set `CSENGINE_TX=0` to disable).

## Components

| Module | Responsibility |
|---|---|
| `src/parser/tokenizer.py` | tokenization, alias/$VAR expansion, obfuscation hints |
| `src/features/extract.py` | 20-feature vector (see `docs/FEATURES.md`) |
| `src/rules/rule_engine.py` | regex rule matching + severity scoring |
| `src/ml/train.py` | GradientBoosting training, evaluation, artifacts |
| `src/llm/explain.py` | Ollama JSON-mode prompt for explanations |
| `src/sandbox/bwrap_check.py` | optional bubblewrap dry-run |
| `src/transaction/paths.py` | SafeShell: target-path extraction from the parsed command |
| `src/transaction/plan.py` | SafeShell: static + LLM-generated undo plans |
| `src/transaction/tx.py` | SafeShell: transaction manager (snapshot/rollback/commit) |
| `src/simulation/run.py` | SafeShell: bwrap simulation + before/after FS diff |
| `src/engine.py` | orchestrator + decision fusion + audit + tx/simulation layers |
| `src/main.py` | CLI (`check`, `run`, `undo`, `tx`, `install-hook`, `status`) |
| `hooks/*` | bash/zsh preexec integration (auto-snapshot on WARN confirm) |
