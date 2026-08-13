"""Transaction manager: snapshot a command's target paths before execution so
they can be restored with `csengine undo`.

Layout under the storage root:
  <tx_id>/
    manifest.json   # command, verdict, snapshots, undo plan, status
    tree/           # copies of snapshotted paths keyed by path hash
"""

import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone

STORAGE_DEFAULT = "~/.csengine/tx"

UNSNAPSHOTABLE = (
    "/", "/bin", "/sbin", "/usr", "/etc", "/boot",
    "/dev", "/proc", "/sys", "/run", "/lib", "/lib64", "/var",
)

_TX_ID_RE = re.compile(r"[0-9a-f]{12}")


class TransactionManager:
    def __init__(self, storage_path=None, max_open=20):
        if storage_path is None:
            storage_path = os.path.expanduser(STORAGE_DEFAULT)
        self.root = os.path.abspath(os.path.expanduser(storage_path))
        os.makedirs(self.root, exist_ok=True)
        self.max_open = max_open

    def _tx_dir(self, tx_id):
        return os.path.join(self.root, tx_id)

    def _tree_dir(self, tx_id):
        return os.path.join(self.root, tx_id, "tree")

    def _manifest_path(self, tx_id):
        return os.path.join(self.root, tx_id, "manifest.json")

    @staticmethod
    def _check_id(tx_id):
        if not _TX_ID_RE.fullmatch(tx_id):
            raise ValueError(f"invalid transaction id: {tx_id!r}")

    def begin(self, command, verdict, risk_score, paths, undo_plan, simulation):
        tx_id = uuid.uuid4().hex[:12]
        tx_dir = self._tx_dir(tx_id)
        os.makedirs(os.path.join(tx_dir, "tree"), exist_ok=True)
        snapshots = self._snapshot(paths, self._tree_dir(tx_id))
        manifest = {
            "id": tx_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "verdict": verdict,
            "risk_score": risk_score,
            "snapshots": snapshots,
            "undo_plan": undo_plan,
            "simulation": simulation,
            "status": "open",
        }
        self._write_manifest(tx_id, manifest)
        self._prune()
        return tx_id

    def _snapshot(self, paths, tree_dir):
        snapshots = []
        for path in dict.fromkeys(paths):
            path = os.path.abspath(os.path.expanduser(path))
            if not self._snapshottable(path) or not os.path.lexists(path):
                continue
            dest = self._tree_rel(tree_dir, path)
            kind = "dir" if os.path.isdir(path) and not os.path.islink(path) else (
                "link" if os.path.islink(path) else "file"
            )
            try:
                if kind == "dir":
                    shutil.copytree(path, dest, symlinks=True, copy_function=shutil.copy2)
                elif kind == "link":
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    link_to = os.readlink(path)
                    try:
                        os.unlink(dest)
                    except FileNotFoundError:
                        pass
                    os.symlink(link_to, dest)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(path, dest)
                stat = os.lstat(path)
                snapshots.append({
                    "path": path,
                    "kind": kind,
                    "size": stat.st_size,
                    "mode": stat.st_mode,
                    "mtime": stat.st_mtime,
                })
            except OSError:
                continue
        return snapshots

    @staticmethod
    def _tree_rel(tree_dir, path):
        digest = hashlib.sha256(path.encode()).hexdigest()[:16]
        return os.path.join(tree_dir, digest)

    def _snapshottable(self, path):
        path = os.path.abspath(path)
        if path in UNSNAPSHOTABLE:
            return False
        if path.startswith(self.root + os.sep) or path == self.root:
            return False
        return not any(path.startswith(root + os.sep) for root in UNSNAPSHOTABLE)

    def rollback(self, tx_id):
        self._check_id(tx_id)
        manifest = self._load_manifest(tx_id)
        if manifest is None:
            raise KeyError(f"no transaction {tx_id!r}")
        tree_dir = self._tree_dir(tx_id)
        restored = []
        for snapshot in manifest.get("snapshots", []):
            path = snapshot["path"]
            src = self._tree_rel(tree_dir, path)
            if not os.path.lexists(src):
                continue
            try:
                self._restore_one(src, path, snapshot["kind"])
                restored.append(path)
            except OSError:
                continue
        for move in manifest.get("undo_plan", {}).get("move_back", []):
            frm, to = move.get("from"), move.get("to")
            if frm and to and os.path.lexists(frm):
                try:
                    os.makedirs(os.path.dirname(to), exist_ok=True)
                    os.replace(frm, to)
                    restored.append(to)
                except OSError:
                    continue
        manifest["status"] = "rolled_back"
        manifest["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        self._write_manifest(tx_id, manifest)
        shutil.rmtree(tree_dir, ignore_errors=True)
        return restored

    @staticmethod
    def _restore_one(src, dest, kind):
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        if kind == "dir":
            if os.path.lexists(dest):
                if os.path.isdir(dest) and not os.path.islink(dest):
                    shutil.rmtree(dest, ignore_errors=True)
                else:
                    os.unlink(dest)
            shutil.copytree(src, dest, symlinks=True, copy_function=shutil.copy2)
        elif kind == "link":
            try:
                os.unlink(dest)
            except FileNotFoundError:
                pass
            os.symlink(os.readlink(src), dest)
        else:
            if os.path.isdir(dest) and not os.path.islink(dest):
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copy2(src, dest)

    def commit(self, tx_id):
        self._check_id(tx_id)
        manifest = self._load_manifest(tx_id)
        if manifest is None:
            return
        manifest["status"] = "committed"
        self._write_manifest(tx_id, manifest)
        shutil.rmtree(self._tree_dir(tx_id), ignore_errors=True)

    def list_open(self):
        open_txs = []
        if not os.path.isdir(self.root):
            return open_txs
        for name in sorted(os.listdir(self.root)):
            if not _TX_ID_RE.fullmatch(name):
                continue
            manifest = self._load_manifest(name)
            if manifest and manifest.get("status") == "open":
                open_txs.append(manifest)
        open_txs.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
        return open_txs

    def _prune(self):
        open_txs = self.list_open()
        if len(open_txs) <= self.max_open:
            return
        for manifest in open_txs[self.max_open:]:
            try:
                self.commit(manifest["id"])
            except OSError:
                continue

    def _load_manifest(self, tx_id):
        path = self._manifest_path(tx_id)
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_manifest(self, tx_id, manifest):
        with open(self._manifest_path(tx_id), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
