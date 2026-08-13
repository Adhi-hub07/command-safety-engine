#!/usr/bin/env bash
# BOSS OS specific installer — wraps setup.sh, installs system packages,
# and builds/installs a .deb for a "government-ready" feel.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[csengine] BOSS OS installer"

# 1. system packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip bubblewrap jq curl dpkg-dev

# 2. Ollama (if missing)
if ! command -v ollama >/dev/null 2>&1; then
  echo "[csengine] installing Ollama"
  curl -fsSL https://ollama.com/install.sh | sh
fi

# 3. standard install
bash "$REPO_DIR/setup.sh"

# 4. optional .deb packaging
if [[ "${CSENGINE_BUILD_DEB:-0}" == "1" ]]; then
  echo "[csengine] building .deb"
  DEB_DIR="$HOME/.csengine/deb/command-safety-engine_1.1_amd64"
  mkdir -p "$DEB_DIR/DEBIAN"
  cat > "$DEB_DIR/DEBIAN/control" <<EOF
Package: command-safety-engine
Version: 1.1
Section: utils
Priority: optional
Architecture: amd64
Depends: python3, python3-venv, python3-pip, jq
Maintainer: Command Safety Engine Team
Description: Offline AI command safety engine for Linux shells
EOF
  cat > "$DEB_DIR/DEBIAN/postinst" <<EOF
#!/bin/sh
set -e
cp -r "$REPO_DIR" /opt/command-safety-engine
cd /opt/command-safety-engine
python3 -m venv /opt/command-safety-engine/.venv
/opt/command-safety-engine/.venv/bin/pip install -r requirements.txt
ln -sf /opt/command-safety-engine/.venv/bin/python /usr/local/bin/csengine
EOF
  chmod +x "$DEB_DIR/DEBIAN/postinst"
  dpkg-deb --build "$DEB_DIR"
  echo "[csengine] built: $HOME/.csengine/deb/command-safety-engine_1.1_amd64.deb"
fi

echo "[csengine] done. Verify offline: run 'nmcli radio all off' then 'csengine status'."
