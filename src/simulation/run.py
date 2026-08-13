"""Simulation-based safety: run a command against copies of its target paths
inside a bubblewrap sandbox and diff the result — the real filesystem is never
touched. The impact report (created/deleted/modified) is the simulation-based
safety guarantee behind WARN/BLOCK decisions.
"""

import hashlib
import os
import shutil
import stat
import subprocess
import tempfile


def bwrap_available():
    return shutil.which("bwrap") is not None


def _hash_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _walk_state(root):
    state = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                st = os.lstat(full)
                kind = (
                    "dir" if stat.S_ISDIR(st.st_mode) else
                    "link" if stat.S_ISLNK(st.st_mode) else "file"
                )
                if kind == "link":
                    state[rel] = ("link", os.readlink(full), st.st_size)
                elif kind == "dir":
                    state[rel] = ("dir", st.st_size, stat.S_IMODE(st.st_mode), st.st_mtime)
                else:
                    state[rel] = ("file", _hash_file(full), stat.S_IMODE(st.st_mode), st.st_mtime)
            except OSError:
                continue
    return state


def _diff(before, after):
    deleted = sorted(set(before) - set(after))
    created = sorted(set(after) - set(before))
    modified = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    return {"created": created, "deleted": deleted, "modified": modified}


def _dir_stats(path):
    """Count entries and total bytes under `path` to bound staging cost."""
    files = 0
    total_bytes = 0
    for dirpath, dirnames, filenames in os.walk(path):
        files += len(dirnames) + len(filenames)
        for name in filenames:
            try:
                total_bytes += os.lstat(os.path.join(dirpath, name)).st_size
            except OSError:
                continue
    return files, total_bytes


MAX_STAGED_FILES = 200
MAX_STAGED_BYTES = 20 * 1024 * 1024


def _stage_parents(paths, limit=8):
    """Return up to `limit` existing parent dirs to stage. Parents are staged even
    when the target itself does not exist yet so file creation is detected, and
    oversized parents are skipped to keep simulation cheap."""
    from src.transaction.tx import UNSNAPSHOTABLE

    seen, out = set(), []
    for path in dict.fromkeys(paths):
        path = os.path.abspath(path)
        parent = os.path.dirname(path) or "/"
        if parent in seen or parent in UNSNAPSHOTABLE or not os.path.isdir(parent):
            continue
        if any(parent.startswith(root + os.sep) for root in UNSNAPSHOTABLE):
            continue
        files, total_bytes = _dir_stats(parent)
        if files > MAX_STAGED_FILES or total_bytes > MAX_STAGED_BYTES:
            continue
        seen.add(parent)
        out.append(parent)
        if len(out) >= limit:
            break
    return out


def simulate(command, paths, timeout_seconds=5):
    """Run `command` against copies of its target paths in a sandbox and report
    the impact. The parent directory of each target is copied and bound over the
    real path, so unlink/create/modify all operate on the copies and the real
    filesystem is never touched.

    Returns {"enabled": True, "exit_code": ..., "impact": {created, deleted, modified}}
    or {"enabled": False, "reason": ...} when simulation is impossible.
    """
    if not bwrap_available():
        return {"enabled": False, "reason": "bubblewrap (bwrap) not installed"}
    parents = _stage_parents(paths)
    if not parents:
        return {"enabled": True, "exit_code": None, "impact": {"created": [], "deleted": [], "modified": []}}
    stage = tempfile.mkdtemp(prefix="csengine-sim-")
    try:
        bwrap_args = [
            "bwrap", "--ro-bind", "/", "/",
            "--dev", "/dev", "--proc", "/proc",
            "--unshare-net", "--unshare-pid", "--unshare-ipc", "--unshare-uts",
            "--die-with-parent",
        ]
        for parent in parents:
            staged = os.path.join(stage, parent.lstrip("/"))
            os.makedirs(os.path.dirname(staged), exist_ok=True)
            shutil.copytree(parent, staged, symlinks=True, copy_function=shutil.copy2)
            bwrap_args += ["--bind", staged, parent]
        before = _walk_state(stage)
        bwrap_args += ["--", "bash", "-c", command]
        proc = subprocess.run(bwrap_args, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        exit_code = proc.returncode
        impact = _diff(before, _walk_state(stage))
    except subprocess.TimeoutExpired:
        impact = _diff(before, _walk_state(stage))
        return {"enabled": True, "exit_code": "timeout", "impact": impact}
    except Exception as exc:
        return {"enabled": False, "reason": str(exc)}
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    return {"enabled": True, "exit_code": exit_code, "impact": impact}
