"""Deterministic rule engine: fast detection of known dangerous patterns."""

import re

import yaml

SEVERITY_WEIGHT = {"critical": 100, "high": 75, "medium": 55, "low": 35}


class RuleEngine:
    def __init__(self, rules_path="config/rules.yaml"):
        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.rules = data.get("rules", [])
        self._compiled = []
        for rule in self.rules:
            patterns = [re.compile(p) for p in rule.get("patterns", [])]
            self._compiled.append((rule, patterns))

    def match(self, command):
        """Return list of matched rule dicts for a command."""
        if not command or not command.strip():
            return []
        matches = []
        for rule, patterns in self._compiled:
            for pattern in patterns:
                if pattern.search(command):
                    matches.append(
                        {
                            "rule_id": rule["id"],
                            "severity": rule["severity"],
                            "category": rule.get("category", ""),
                            "mitre": rule.get("mitre", ""),
                            "explanation": rule.get("explanation", ""),
                            "alternative": rule.get("alternative", ""),
                        }
                    )
                    break
        return matches

    def score(self, matches):
        """Blend matched rule severities into a 0-100 risk score."""
        if not matches:
            return 0
        weights = [SEVERITY_WEIGHT.get(m["severity"], 40) for m in matches]
        return min(100, max(weights) + int(0.3 * sum(weights) * (len(weights) - 1) / max(1, len(weights))))


def load_whitelist(path="config/whitelist.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [str(item) for item in data.get("whitelist", [])]
