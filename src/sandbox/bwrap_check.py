"""Optional bubblewrap sandbox dry-run for risky commands."""

import shutil
import subprocess


def bwrap_available():
    return shutil.which("bwrap") is not None


def dry_run(command, timeout_seconds=3):
    """Run a command inside a bubblewrap sandbox with no network and no writes.

    Returns {"enabled": True, "exit_code": ..., "output": ...} or raises RuntimeError.
    """
    if not bwrap_available():
        raise RuntimeError("bubblewrap (bwrap) not installed")
    cmd = [
        "bwrap",
        "--ro-bind", "/", "/",
        "--dev", "/dev",
        "--proc", "/proc",
        "--unshare-net",
        "--die-with-parent",
        "--",
        "bash", "-c", command,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {"enabled": True, "exit_code": "timeout", "output": "command timed out in sandbox"}
    return {"enabled": True, "exit_code": proc.returncode, "output": (proc.stdout + proc.stderr)[:500]}
