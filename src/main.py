#!/usr/bin/env python3
"""Command Safety Engine CLI entrypoint.

Usage:
  csengine check "<command>"           analyze one command
  csengine check --json "<command>"    analyze, print JSON
  csengine install-hook [bash|zsh]     install the shell preexec hook
  csengine status                      show model / LLM availability
  csengine --version
Exit codes: 0=ALLOW, 1=WARN, 2=BLOCK (usable by shell hooks).
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

VERSION = "1.1.0"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="csengine", description="Offline AI command safety engine")
    parser.add_argument("--version", action="version", version=f"csengine {VERSION}")
    sub = parser.add_subparsers(dest="cmd")

    check = sub.add_parser("check", help="analyze a command")
    check.add_argument("command", nargs="+", help="the shell command to analyze")
    check.add_argument("--json", action="store_true", help="output JSON only")
    check.add_argument("--audit", action="store_true", help="write to audit log")
    check.add_argument("--tx", action="store_true", help="begin a snapshot transaction for risky commands")

    run = sub.add_parser("run", help="run a command under an automatic undo snapshot")
    run.add_argument("command", nargs="+", help="the shell command to run")
    run.add_argument("--force", action="store_true", help="run even if the engine BLOCKs (still snapshotted)")

    undo = sub.add_parser("undo", help="roll back a snapshot transaction")
    undo.add_argument("tx_id", help="transaction id, or 'last'")

    tx = sub.add_parser("tx", help="manage snapshot transactions")
    tx_sub = tx.add_subparsers(dest="txcmd")
    tx_sub.add_parser("list", help="list open transactions")
    tx_commit = tx_sub.add_parser("commit", help="discard a snapshot")
    tx_commit.add_argument("tx_id")
    tx_rollback = tx_sub.add_parser("rollback", help="restore a snapshot")
    tx_rollback.add_argument("tx_id")

    install = sub.add_parser("install-hook", help="install the shell hook")
    install.add_argument("shell", nargs="?", default="bash", choices=["bash", "zsh"])

    sub.add_parser("status", help="show engine status")

    args = parser.parse_args(argv)

    if args.cmd == "check":
        command = " ".join(args.command)
        return run_check(command, json_out=args.json, audit=args.audit, tx=args.tx)
    if args.cmd == "run":
        return run_guarded(" ".join(args.command), force=args.force)
    if args.cmd == "undo":
        return undo_tx(args.tx_id)
    if args.cmd == "tx":
        if args.txcmd == "commit":
            return commit_tx(args.tx_id)
        if args.txcmd == "rollback":
            return undo_tx(args.tx_id)
        return list_tx()
    if args.cmd == "install-hook":
        return install_hook(args.shell)
    if args.cmd == "status":
        return show_status()
    parser.print_help()
    return 0


def run_check(command, json_out=False, audit=False, tx=False):
    from src.engine import CommandSafetyEngine
    from src.output.formatter import render_rich, to_json

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    result = engine.analyze(command)
    if audit:
        engine.audit(result)
    if tx and result["final_decision"]["verdict"] != "ALLOW":
        tx_id = engine.begin_transaction(result)
        print(f"[safeshell] undo snapshot tx={tx_id} (restore with `csengine undo {tx_id}`)", file=sys.stderr)
    if json_out:
        print(to_json(result))
    else:
        render_rich(result)
    verdict = result["final_decision"]["verdict"]
    return {"ALLOW": 0, "WARN": 1, "BLOCK": 2}[verdict]


def run_guarded(command, force=False):
    """Execute a command inside a transaction: analyze, snapshot, simulate,
    ask, run, and leave the snapshot open for `csengine undo`."""
    import subprocess

    from src.engine import CommandSafetyEngine
    from src.output.formatter import render_rich

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    result = engine.analyze(command)
    render_rich(result)
    verdict = result["final_decision"]["verdict"]

    plan = result.get("transaction", {}).get("undo_plan", {})
    for step in plan.get("steps", [])[:5]:
        print(f"  undo: {step['description']}")

    sim = result.get("simulation", {})
    if sim.get("enabled"):
        impact = sim.get("impact", {})
        print(f"  simulation: {len(impact['deleted'])} deleted, "
              f"{len(impact['modified'])} modified, {len(impact['created'])} created")
    else:
        print(f"  simulation: unavailable ({sim.get('reason', 'n/a')})")

    if verdict == "BLOCK" and not force:
        print("REFUSED: dangerous command. Use --force to run under a snapshot.")
        return 2

    try:
        answer = input(f"Run `{command}` with an automatic undo snapshot? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() not in ("y", "yes"):
        print("cancelled.")
        return 1

    tx_id = engine.begin_transaction(result, command=command)
    code = subprocess.run(command, shell=True, check=False).returncode
    print(f"[safeshell] exit={code} — snapshot tx={tx_id} is open. "
          f"Roll back with `csengine undo {tx_id}`, keep with `csengine tx commit {tx_id}`.")
    return code


def undo_tx(tx_id):
    from src.engine import CommandSafetyEngine

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    if tx_id == "last":
        open_txs = engine.list_transactions()
        if not open_txs:
            print("no open transactions to undo.")
            return 1
        tx_id = open_txs[0]["id"]
    try:
        restored = engine.rollback_transaction(tx_id)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}")
        return 1
    print(f"rolled back tx={tx_id}: restored {len(restored)} path(s)")
    for path in restored:
        print(f"  restored  {path}")
    return 0


def commit_tx(tx_id):
    from src.engine import CommandSafetyEngine

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    try:
        engine.commit_transaction(tx_id)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    print(f"committed tx={tx_id}: snapshot discarded.")
    return 0


def list_tx():
    from src.engine import CommandSafetyEngine

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    open_txs = engine.list_transactions()
    if not open_txs:
        print("no open transactions.")
        return 0
    for tx in open_txs:
        snapshots = tx.get("snapshots", [])
        print(f"{tx['id']}  {tx['timestamp']}  {tx['verdict']:<5} risk={tx['risk_score']}  "
              f"snap={len(snapshots)}  cmd={tx['command']}")
    return 0


def install_hook(shell):
    hooks_dir = os.path.join(PROJECT_ROOT, "hooks")
    if shell == "zsh":
        source_line = f'[[ -f "{hooks_dir}/csengine.zsh" ]] && source "{hooks_dir}/csengine.zsh"'
        rc = os.path.expanduser("~/.zshrc")
    else:
        source_line = f'[[ -f "{hooks_dir}/csengine.bash" ]] && source "{hooks_dir}/csengine.bash"'
        rc = os.path.expanduser("~/.bashrc")

    if not os.path.exists(rc):
        open(rc, "a").close()

    with open(rc, "r", encoding="utf-8") as f:
        existing = f.read()
    if "csengine.bash" in existing or "csengine.zsh" in existing:
        print(f"Hook already installed in {rc}")
        return 0
    with open(rc, "a", encoding="utf-8") as f:
        f.write("\n# Command Safety Engine hook\n" + source_line + "\n")
    print(f"Installed {shell} hook into {rc}. Restart your shell or run: source {rc}")
    return 0


def show_status():
    from src.engine import CommandSafetyEngine

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    print(f"csengine {VERSION}")
    print(f"Rule engine  : {len(engine.rules.rules)} rules loaded")
    print(f"ML model     : {'loaded' if engine.model is not None else 'NOT loaded (run python -m src.ml.train)'}")
    llm_state = "unavailable (install ollama)"
    if engine.llm is not None:
        if engine.llm.is_available():
            llm_state = f"available ({engine.llm.model})"
        else:
            llm_state = f"server down (start ollama, model: {engine.llm.model})"
    print(f"LLM (Ollama) : {llm_state}")
    print(f"Whitelist    : {len(engine.whitelist)} safe patterns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
