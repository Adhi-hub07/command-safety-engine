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

VERSION = "1.0.0"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="csengine", description="Offline AI command safety engine")
    parser.add_argument("--version", action="version", version=f"csengine {VERSION}")
    sub = parser.add_subparsers(dest="cmd")

    check = sub.add_parser("check", help="analyze a command")
    check.add_argument("command", nargs="+", help="the shell command to analyze")
    check.add_argument("--json", action="store_true", help="output JSON only")
    check.add_argument("--audit", action="store_true", help="write to audit log")

    install = sub.add_parser("install-hook", help="install the shell hook")
    install.add_argument("shell", nargs="?", default="bash", choices=["bash", "zsh"])

    sub.add_parser("status", help="show engine status")

    args = parser.parse_args(argv)

    if args.cmd == "check":
        command = " ".join(args.command)
        return run_check(command, json_out=args.json, audit=args.audit)
    if args.cmd == "install-hook":
        return install_hook(args.shell)
    if args.cmd == "status":
        return show_status()
    parser.print_help()
    return 0


def run_check(command, json_out=False, audit=False):
    from src.engine import CommandSafetyEngine
    from src.output.formatter import render_rich, to_json

    engine = CommandSafetyEngine(project_root=PROJECT_ROOT)
    result = engine.analyze(command)
    if audit:
        engine.audit(result)
    if json_out:
        print(to_json(result))
    else:
        render_rich(result)
    verdict = result["final_decision"]["verdict"]
    return {"ALLOW": 0, "WARN": 1, "BLOCK": 2}[verdict]


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
