# BOSS OS Integration

BOSS OS (Bharat Operating System Solutions) is C-DAC's indigenous
GNU/Linux distribution, Debian-based and used in Indian government
systems. The engine installs on BOSS OS the same way as Ubuntu.

## Install

```bash
# quick path
bash install-boss-os.sh

# or build the .deb
CSENGINE_BUILD_DEB=1 bash install-boss-os.sh
sudo dpkg -i ~/.csengine/deb/command-safety-engine_1.1_amd64.deb
```

What the installer does:

1. `apt-get install python3 python3-venv python3-pip bubblewrap jq curl dpkg-dev`
2. Installs Ollama (if absent), pulls `qwen2.5:3b-instruct-q4_K_M`
3. Creates an isolated venv at `~/.csengine/venv` (never touches BOSS OS
   system Python, which is tied to system services)
4. Generates the labeled dataset and trains the GradientBoosting classifier
5. Installs the `csengine` command and bash/zsh preexec hook

## Verify offline operation

```bash
nmcli radio all off          # or: sudo ip link set <iface> down
csengine status              # LLM available, all layers loaded
csengine check "rm -rf /"    # BLOCK — works with zero network
csengine check "git status"  # ALLOW — instant (whitelisted)
nmcli radio all on
```

This air-gapped proof is a core demo point: government systems often run
on restricted networks, and our engine is fully functional offline.

## .deb packaging notes

- `postinst` copies the repo to `/opt/command-safety-engine`, creates a
  venv, installs deps, and symlinks `/usr/local/bin/csengine`.
- Architecture is `amd64`; adjust for aarch64 (RISC-V / ARM) builds.
- The .deb is optional polish — the script path is the reliable demo path.

## Known BOSS OS quirks

| Quirk | Handling |
|---|---|
| system Python tied to OS packages | isolated venv in `~/.csengine/` |
| older `apt` caches | `apt-get update` before install |
| no `python3-venv` preinstalled | installed explicitly in step 1 |
| read-only `/opt` on some govt builds | fall back to `~/.csengine/` install |
