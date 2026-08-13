import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.run import _diff, _walk_state, simulate
from src.transaction.paths import extract_paths
from src.transaction.plan import static_undo_plan
from src.transaction.tx import TransactionManager


def test_extract_rm_paths(tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("hello")
    paths = extract_paths(f"rm -rf {target}", cwd=str(tmp_path))
    assert os.path.abspath(str(target)) in paths


def test_extract_redirect_target(tmp_path):
    out = tmp_path / "out.txt"
    paths = extract_paths(f"echo hi > {out}", cwd=str(tmp_path))
    assert os.path.abspath(str(out)) in paths


def test_extract_chmod_drops_mode(tmp_path):
    target = tmp_path / "x"
    target.write_text("x")
    paths = extract_paths(f"chmod -R 777 {target}", cwd=str(tmp_path))
    assert os.path.abspath(str(target)) in paths


def test_extract_skips_read_redirects(tmp_path):
    target = tmp_path / "in.txt"
    target.write_text("x")
    paths = extract_paths(f"cat < {target}", cwd=str(tmp_path))
    assert os.path.abspath(str(target)) not in paths


def test_extract_sudo_prefix(tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("x")
    paths = extract_paths(f"sudo rm {target}", cwd=str(tmp_path))
    assert os.path.abspath(str(target)) in paths


def test_undo_plan_rm_has_restore(tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("hello")
    plan = static_undo_plan(f"rm {target}", [os.path.abspath(str(target))])
    assert plan["steps"]
    assert any(s["action"] == "restore" for s in plan["steps"])


def test_undo_plan_mv_has_move_back(tmp_path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.txt"
    src.write_text("x")
    plan = static_undo_plan(f"mv {src} {dst}", [os.path.abspath(str(src)), os.path.abspath(str(dst))])
    assert plan["steps"]
    assert plan["move_back"], "mv must produce a move-back step"


def test_tx_rollback_restores_deleted_file(tmp_path):
    root = tmp_path / "txroot"
    target = tmp_path / "data" / "important.txt"
    target.parent.mkdir()
    target.write_text("precious")
    txm = TransactionManager(storage_path=str(root))
    tx_id = txm.begin("rm important.txt", "WARN", 55, [str(target)], {"steps": []}, {})
    os.remove(target)
    assert not target.exists()
    txm.rollback(tx_id)
    assert target.read_text() == "precious"


def test_tx_rollback_restores_mode(tmp_path):
    root = tmp_path / "txroot"
    target = tmp_path / "secret.txt"
    target.write_text("s")
    os.chmod(target, 0o644)
    txm = TransactionManager(storage_path=str(root))
    tx_id = txm.begin("chmod 777 secret.txt", "WARN", 60, [str(target)], {}, {})
    os.chmod(target, 0o777)
    txm.rollback(tx_id)
    assert os.stat(target).st_mode & 0o777 == 0o644


def test_tx_commit_discards(tmp_path):
    root = tmp_path / "txroot"
    target = tmp_path / "keep.txt"
    target.write_text("x")
    txm = TransactionManager(storage_path=str(root))
    tx_id = txm.begin("touch keep.txt", "WARN", 50, [str(target)], {}, {})
    txm.commit(tx_id)
    assert txm.list_open() == []


def test_tx_list_open(tmp_path):
    root = tmp_path / "txroot"
    txm = TransactionManager(storage_path=str(root))
    tx_id = txm.begin("chmod 777 f", "WARN", 60, [], {}, {})
    assert tx_id in [t["id"] for t in txm.list_open()]


def test_tx_invalid_id_rejected(tmp_path):
    txm = TransactionManager(storage_path=str(tmp_path / "txroot"))
    with pytest.raises(ValueError):
        txm.rollback("../etc")


def test_diff_detects_changes():
    before = {"f.txt": ("file", "abc", 0o644, 1.0)}
    after = {
        "f.txt": ("file", "xyz", 0o644, 1.0),
        "new.txt": ("file", "n", 0o644, 1.0),
    }
    impact = _diff(before, after)
    assert "f.txt" in impact["modified"]
    assert "new.txt" in impact["created"]
    assert impact["deleted"] == []


def test_diff_detects_deletion():
    before = {"gone.txt": ("file", "a", 0o644, 1.0)}
    impact = _diff(before, {})
    assert impact["deleted"] == ["gone.txt"]


def test_walk_state_hash_changes(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("one")
    before = _walk_state(str(tmp_path))
    f.write_text("two")
    after = _walk_state(str(tmp_path))
    assert before["a.txt"] != after["a.txt"]


def test_simulate_shape(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    result = simulate(f"cat {f}", [str(f)])
    if result["enabled"]:
        assert set(result["impact"]) == {"created", "deleted", "modified"}
    else:
        assert "reason" in result


def test_simulate_predicts_deletion(tmp_path):
    target = tmp_path / "doomed.txt"
    target.write_text("bye")
    result = simulate(f"rm {target}", [str(target)])
    if result["enabled"]:
        deleted = [p for p in result["impact"]["deleted"]]
        assert any("doomed.txt" in p for p in deleted)
