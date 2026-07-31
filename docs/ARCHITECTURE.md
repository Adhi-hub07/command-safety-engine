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
                    │  3. Rule Engine (rules.yaml, 20 rule groups)         │
                    │     fast deterministic match  ──┐                    │
                    │        │                        │ severity+MITRE    │
                    │        ▼                        ▼                   │
                    │  4. Feature Extraction (20 features)                 │
                    │        │                                             │
                    │        ▼                                             │
                    │  5. ML Classifier (RandomForest, 3 classes)          │
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

## Components

| Module | Responsibility |
|---|---|
| `src/parser/tokenizer.py` | tokenization, alias/$VAR expansion, obfuscation hints |
| `src/features/extract.py` | 20-feature vector (see `docs/FEATURES.md`) |
| `src/rules/rule_engine.py` | regex rule matching + severity scoring |
| `src/ml/train.py` | RandomForest training, evaluation, artifacts |
| `src/llm/explain.py` | Ollama JSON-mode prompt for explanations |
| `src/sandbox/bwrap_check.py` | optional bubblewrap dry-run |
| `src/engine.py` | orchestrator + decision fusion + audit |
| `src/main.py` | CLI (`check`, `install-hook`, `status`) |
| `hooks/*` | bash/zsh preexec integration |
