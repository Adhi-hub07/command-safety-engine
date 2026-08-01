#!/usr/bin/env python3
"""Real-pty interactive hook test.

Feeds commands into a real interactive shell (bash, and zsh if installed)
under a pty and verifies the csengine hook blocks a dangerous command.

Run:  python scripts/test_hook_pty.py        (from repo root)
Or:   python3 scripts/test_hook_pty.py
Requires: the engine reachable via CSENGINE_BIN, `csengine` on PATH, or
~/.csengine/bin/csengine (the wrapper setup.sh creates).
"""
import os
import pty
import select
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_engine_bin():
    for cand in (
        os.environ.get("CSENGINE_BIN", ""),
        shutil.which("csengine") or "",
        os.path.expanduser("~/.csengine/bin/csengine"),
        os.path.join(ROOT, "src", "main.py"),
    ):
        if cand and os.path.exists(cand):
            return cand
    return None


ENGINE = find_engine_bin()
if not ENGINE:
    print("FAIL: no csengine binary found")
    sys.exit(1)

DANGEROUS = "dd if=/dev/zero of=/dev/sda bs=512 count=1"  # BLOCK verdict


def run_pty(shell_args, cmds, env_extra, setup=None):
    master, slave = pty.openpty()
    pid = os.fork()
    if pid == 0:
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.close(master)
        if setup:
            setup()
        env = dict(os.environ)
        env.update(env_extra)
        os.execvpe(shell_args[0], shell_args, env)
    os.close(slave)
    time.sleep(1.0)
    for c in cmds:
        os.write(master, c.encode())
        time.sleep(1.5)
    buf = b""
    deadline = time.time() + 15
    while time.time() < deadline:
        r, _, _ = select.select([master], [], [], 0.5)
        if master in r:
            try:
                d = os.read(master, 65536)
            except OSError:
                break
            if not d:
                break
            buf += d
    try:
        os.close(master)
    except OSError:
        pass
    for _ in range(20):
        wpid, _ = os.waitpid(pid, os.WNOHANG)
        if wpid:
            break
        time.sleep(0.2)
    else:
        os.kill(pid, 15)
        os.waitpid(pid, 0)
    return buf.decode("utf-8", "replace")


def test_shell(name, shell_args, env_extra, zdotdir=None):
    # WARN command: first attempt is blocked, second confirms (bash: retype;
    # zsh: bare Enter confirms the still-buffered line). It targets a missing
    # file so a confirmed run proves itself with a chmod error message.
    warn_cmd = "chmod 777 /tmp/csengine_nonexistent"
    confirm = warn_cmd if name == "bash" else "\r"

    def setup():
        if zdotdir:
            os.makedirs(zdotdir, exist_ok=True)
            hook = os.path.join(ROOT, "hooks", "csengine." + name)
            with open(os.path.join(zdotdir, ".zshrc"), "w") as f:
                f.write(f"source {hook}\n")
                f.write("export PATH=\"$HOME/.csengine/bin:$PATH\"\n")
    if zdotdir:
        env_extra = dict(env_extra)
        env_extra["ZDOTDIR"] = zdotdir
    cmds = ["echo hello\r", "git status\r", warn_cmd + "\r", confirm + "\r", DANGEROUS + "\r", "exit\r"]
    s = run_pty(shell_args, cmds, env_extra, setup=setup)
    with open(f"/tmp/csengine_hook_test_{name}.log", "w") as f:
        f.write(s)
    fail = 0
    if "hello" in s:
        print(f"PASS [{name}] echo output")
    else:
        print(f"FAIL [{name}] echo output"); fail += 1
    if "BLOCKED" in s:
        print(f"PASS [{name}] BLOCKED message shown")
    else:
        print(f"FAIL [{name}] no BLOCKED message"); fail += 1
    if "dd:" in s:
        print(f"FAIL [{name}] dangerous dd executed"); fail += 1
    else:
        print(f"PASS [{name}] dangerous dd did NOT execute")
    if "WARNING" in s and "cannot access" in s:
        print(f"PASS [{name}] WARN retype-confirm flow works")
    else:
        print(f"FAIL [{name}] WARN retype-confirm flow (WARNING={'WARNING' in s}, chmod-err={'cannot access' in s})")
        fail += 1
    return fail


def main():
    print(f"engine: {ENGINE}")
    fails = 0
    env_common = {"CSENGINE_BIN": ENGINE}
    if shutil.which("bash") and not os.environ.get("CSENGINE_SKIP_BASH"):
        fails += test_shell("bash", ["bash", "-i"], env_common)
    else:
        print("skip bash")
    if shutil.which("zsh"):
        fails += test_shell("zsh", ["zsh", "-i"], env_common, zdotdir="/tmp/csengine_zsh_test")
    else:
        print("skip zsh (not installed)")
    print("RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
