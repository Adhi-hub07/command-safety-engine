"""Undo-plan generation: deterministic static reversal plus optional LLM insight.

The static plan is always computed so recovery works offline. When a local LLM
is available it is asked to suggest recovery actions too; the static steps stay
authoritative so a bad model output can never corrupt the undo path.
"""

from src.parser import tokenizer

_LEADERS = ("sudo", "env", "command", "nohup", "time")


def static_undo_plan(command, paths):
    """Return {"steps": [...], "move_back": [...], "source": "static"}."""
    steps = []
    move_back = []
    for segment in tokenizer.split_pipeline_commands(command):
        words = [t.text for t in tokenizer.tokenize(segment) if t.kind == "word"]
        while words and words[0] in _LEADERS:
            words.pop(0)
        if not words:
            continue
        base = words[0]
        positional = [w for w in words[1:] if not w.startswith("-")]
        if base in ("rm", "rmdir", "unlink"):
            for p in paths:
                steps.append({"action": "restore", "target": p, "description": f"restore {p} from snapshot"})
        elif base in ("mv", "cp", "install"):
            if len(positional) >= 2:
                sources, dest = positional[:-1], positional[-1]
                for src in sources:
                    steps.append({"action": "restore", "target": src, "description": f"restore {src} from snapshot"})
                    move_back.append({"from": dest, "to": src})
            else:
                for p in paths:
                    steps.append({"action": "restore", "target": p, "description": f"restore {p} from snapshot"})
        elif base in ("chmod", "chown", "chgrp"):
            for p in paths:
                steps.append({"action": "restore", "target": p, "description": f"restore permissions/ownership of {p} from snapshot"})
        elif base in ("touch", "truncate", "tee", "dd"):
            for p in paths:
                steps.append({"action": "restore", "target": p, "description": f"restore {p} from snapshot"})
    if not steps:
        steps = [{"action": "restore", "target": p, "description": f"restore {p} from snapshot"} for p in paths]
    return {"steps": steps, "move_back": move_back, "source": "static"}


def plan_with_llm(llm, command, plan):
    """Merge LLM-suggested recovery steps into a static plan (static stays authoritative)."""
    plan = dict(plan)
    try:
        ai_steps = llm.undo_plan(command)
    except Exception:
        ai_steps = []
    if ai_steps:
        plan["ai_steps"] = ai_steps
        plan["source"] = "static+llm"
    return plan
