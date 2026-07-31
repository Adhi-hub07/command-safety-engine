"""Output formatting: JSON + rich terminal rendering."""

import json

VERDICT_COLORS = {"ALLOW": "green", "WARN": "yellow", "BLOCK": "red"}

LABEL_RISK_TEXT = {
    "safe": "This command appears safe.",
    "risky": "This command may be risky. Review before running.",
    "destructive": "This command is destructive. Do not run without confirmation.",
}


def to_json(result, pretty=True):
    return json.dumps(result, indent=2, ensure_ascii=False) if pretty else json.dumps(result)


def render_rich(result, color=True):
    """Render the decision as a rich-formatted terminal panel."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    decision = result["final_decision"]
    verdict = decision["verdict"]
    verdict_color = VERDICT_COLORS.get(verdict, "white")

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_row("Command", result["command"])
    table.add_row("Verdict", f"[{verdict_color} bold]{verdict}[/{verdict_color} bold]")
    table.add_row("Risk score", f"{decision['risk_score']}/100")
    if result["rule_engine"]["matched"]:
        rules = result["rule_engine"]["rules"][0]
        table.add_row("Matched rule", rules["rule_id"])
        table.add_row("Category", rules.get("category", ""))
        if rules.get("mitre"):
            table.add_row("MITRE", rules["mitre"])
    if result["ml_classifier"].get("confidence"):
        table.add_row("ML prediction", f"{result['ml_classifier']['predicted_label']} "
                                       f"({result['ml_classifier']['confidence']:.0%})")
    if result["llm_explanation"].get("summary"):
        table.add_row("Explanation", result["llm_explanation"]["summary"])
    if result["llm_explanation"].get("suggested_alternative"):
        table.add_row("Safer alternative", result["llm_explanation"]["suggested_alternative"])
    table.add_row("Latency", f"{decision['latency_ms']} ms")

    console.print(Panel(table, title="Command Safety Engine", border_style=verdict_color))
