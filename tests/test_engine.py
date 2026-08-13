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


def test_ml_only_risky_warns():
    """A novel risky command with no matching rule must still WARN (ML carries the risk)."""
    result = make_engine().analyze("rm -rf build/")
    assert result["final_decision"]["verdict"] == "WARN"
    assert result["final_decision"]["risk_score"] >= 45


def test_ml_only_destructive_blocks():
    """A destructive command not covered by rules is still blocked via ML at high confidence."""
    result = make_engine().analyze("wipefs -a /dev/sda")
    assert result["final_decision"]["verdict"] == "BLOCK"


class _FakeLLM:
    def __init__(self):
        self.calls = 0

    def is_available(self):
        return True

    def explain(self, command, rule_matches=None):
        self.calls += 1
        return {"summary": "explained", "alternative": "safer alternative"}


def _explain_with(engine, confidence):
    fake = _FakeLLM()
    engine.llm = fake
    engine._explain(
        "dummy cmd",
        "dummy cmd",
        [],
        {"confidence": confidence, "predicted_label": "risky"},
        {"whitelist_match": False},
    )
    return fake


def test_llm_called_when_ambiguous():
    """LLM is consulted when ML confidence is below the ambiguity threshold."""
    engine = make_engine()
    fake = _explain_with(engine, confidence=0.5)
    assert fake.calls == 1


def test_llm_not_called_when_confident():
    """LLM is skipped when the ML model is confident."""
    engine = make_engine()
    fake = _explain_with(engine, confidence=0.95)
    assert fake.calls == 0


def test_llm_demo_command_is_ambiguous():
    """The demo scene-10 command must actually reach the LLM path (no rule, low confidence)."""
    result = make_engine().analyze("xxd -r -p <<< '77686f616d69'")
    assert not result["rule_engine"]["matched"]
    assert result["ml_classifier"]["confidence"] < 0.65


def test_transaction_layers_present():
    """SafeShell layers: snapshot paths + undo plan + simulation on every result."""
    result = make_engine().analyze("rm -rf build/")
    assert "transaction" in result
    assert isinstance(result["transaction"]["snapshot_paths"], list)
    assert "steps" in result["transaction"]["undo_plan"]
    assert "simulation" in result


def test_simulation_only_for_risky():
    """ALLOW commands must skip simulation to keep the fast path fast."""
    result = make_engine().analyze("git status")
    assert result["final_decision"]["verdict"] == "ALLOW"
    assert result["simulation"]["enabled"] is False


def test_begin_and_rollback_transaction(tmp_path):
    """End-to-end: snapshot a risky command, delete the file, roll back, verify content."""
    engine = make_engine()
    target = tmp_path / "important.txt"
    target.write_text("precious")
    result = engine.analyze(f"rm {target}")
    result["transaction"]["snapshot_paths"] = [str(target)]
    engine.config.setdefault("transaction", {})["storage_path"] = str(tmp_path / "tx")
    tx_id = engine.begin_transaction(result, command=f"rm {target}")
    os.remove(target)
    assert not target.exists()
    restored = engine.rollback_transaction(tx_id)
    assert str(target) in restored
    assert target.read_text() == "precious"


def test_begin_and_commit_transaction(tmp_path):
    engine = make_engine()
    target = tmp_path / "keep.txt"
    target.write_text("x")
    result = engine.analyze(f"touch {target}")
    result["transaction"]["snapshot_paths"] = [str(target)]
    engine.config["transaction"]["storage_path"] = str(tmp_path / "tx")
    tx_id = engine.begin_transaction(result, command=f"touch {target}")
    engine.commit_transaction(tx_id)
    assert engine.list_transactions() == []


def test_blocked_fork_bomb_is_never_simulated():
    engine = make_engine()
    result = engine.analyze(":(){ :|:& };:")
    assert result["final_decision"]["verdict"] == "BLOCK"
    assert result["transaction"]["snapshot_paths"] == []
    assert result["simulation"]["enabled"] is False
