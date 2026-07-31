# Command Safety Engine
> Offline AI guard for Linux shells — C-DAC Secure OS Hackathon 2026, Track 1 (AI @ Application Level)

Detects dangerous Linux commands **before** they execute, explains the risk in plain English, and suggests safer alternatives. Fully offline, open-source, and runs on a normal laptop.

```
Command → Rule Engine → ML Classifier → Local LLM (Qwen 2.5 3B) → Allow / Warn / Block
```

- **100% offline** — no cloud APIs, aligned with India's sovereign OS (AtmaNirbhar) mission
- **Hybrid AI** — deterministic rules + scikit-learn classifier + local LLM explanation
- **<1ms** fast path for common commands (rules+ML, measured 0.47 ms); full pipeline ~56 ms; LLM only invoked for ambiguous cases
- **Works on BOSS OS** (Indian government Linux) and standard Ubuntu/Debian
- **Educates** — every warning explains why, maps to MITRE ATT&CK, and suggests a safer rewrite

## Quick start

```bash
bash setup.sh            # installs deps + Ollama + shell hooks
csengine check "rm -rf /"
csengine check "git pull"
```

## Install on BOSS OS

```bash
bash install-boss-os.sh
```

## Project layout

```
command-safety-engine/
├── config/            # rules.yaml, whitelist.yaml, config.yaml
├── data/              # labeled command dataset + synthetic generator
├── src/
│   ├── parser/        # bashlex-based command tokenizer
│   ├── features/      # 20 feature extractor
│   ├── rules/         # deterministic rule engine
│   ├── ml/            # training + evaluation scripts
│   ├── llm/           # local Ollama explanation layer
│   ├── sandbox/       # optional bubblewrap dry-run
│   ├── output/        # JSON + rich CLI formatting
│   └── engine.py      # orchestrator
├── hooks/             # bash/zsh preexec hooks
├── scripts/           # data labeling, latency benchmark, demo seeds
├── tests/             # pytest suite
└── docs/              # architecture, features, BOSS OS integration
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Feature dictionary](docs/FEATURES.md)
- [BOSS OS integration](docs/BOSS_OS_INTEGRATION.md)

## License
MIT
