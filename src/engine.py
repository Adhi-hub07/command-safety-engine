"""Command risk orchestrator: rules -> ML -> LLM -> decision."""

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone

import yaml

from src.features.extract import FEATURE_NAMES, extract_features, feature_vector
from src.parser import tokenizer
from src.rules.rule_engine import RuleEngine, load_whitelist

VERDICT_ORDER = {"ALLOW": 0, "WARN": 1, "BLOCK": 2}
WRAPPER_RE = re.compile(r'^\s*(?:sudo\s+)?(?:bash|sh|zsh|dash|ksh)\s+-[a-z]*c[a-z]*\s+(["\'])(.*?)\1\s*$', re.DOTALL)
MAX_UNWRAP_DEPTH = 2


class CommandSafetyEngine:
    def __init__(self, config_path=None, project_root="."):
        if config_path is None:
            config_path = os.path.join(project_root, "config", "config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.project_root = project_root
        self.rules = RuleEngine(os.path.join(project_root, self.config["rules"]["path"]))
        self.whitelist = load_whitelist(os.path.join(project_root, self.config["rules"]["whitelist_path"]))
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self._load_ml()
        self._load_llm()

    def _load_ml(self):
        if not self.config.get("ml", {}).get("enabled", True):
            return
        try:
            import joblib
            model_path = os.path.join(self.project_root, self.config["model"]["path"])
            vectorizer_path = os.path.join(self.project_root, self.config["model"]["vectorizer_path"])
            labels_path = os.path.join(self.project_root, self.config["model"]["label_encoder_path"])
            if os.path.exists(model_path) and os.path.exists(vectorizer_path) and os.path.exists(labels_path):
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.label_encoder = joblib.load(labels_path)
            else:
                self._model_notice = f"ML model not found at {model_path}; run `python -m src.ml.train`"
        except ImportError:
            self._model_notice = "joblib not installed"

    def _load_llm(self):
        self.llm = None
        llm_cfg = self.config.get("llm", {})
        if not llm_cfg.get("enabled", True):
            return
        try:
            from src.llm.explain import LLMExplainer
            self.llm = LLMExplainer(
                model=llm_cfg.get("model"),
                base_url=llm_cfg.get("base_url"),
                timeout_seconds=llm_cfg.get("timeout_seconds", 4),
            )
        except ImportError:
            self.llm = None

    def analyze(self, command, aliases=None, _depth=0):
        """Full pipeline analysis. Returns the decision JSON."""
        start = time.perf_counter()
        original = command
        expanded = tokenizer.expand_command(command, aliases=aliases)
        normalized = tokenizer.normalize_space(expanded)

        rule_matches = self.rules.match(normalized)
        rule_score = self.rules.score(rule_matches)
        features = extract_features(normalized, whitelist=self.whitelist)

        ml_result = self._classify(normalized, features)
        llm_explanation = self._explain(original, normalized, rule_matches, ml_result, features)

        risk_score = self._blend_risk(rule_score, ml_result)
        verdict = self._decide(risk_score, rule_matches, ml_result)

        # Unwrap one level of bash -c '...' / sh -c "..." so a destructive payload
        # hidden behind a wrapper (bash -c 'rm -rf /') is still caught.
        payload = self._unwrap_payload(normalized)
        if payload and _depth < MAX_UNWRAP_DEPTH:
            inner = self.analyze(payload, aliases=aliases, _depth=_depth + 1)
            inner_decision = inner["final_decision"]
            inner_rules = inner["rule_engine"]["rules"]
            seen = {r["rule_id"] for r in rule_matches}
            rule_matches = rule_matches + [r for r in inner_rules if r["rule_id"] not in seen]
            risk_score = max(risk_score, inner_decision["risk_score"])
            if inner_decision["verdict"] == "BLOCK":
                verdict = {"verdict": "BLOCK", "risk_score": risk_score, "requires_confirmation": True}
            elif verdict["verdict"] == "ALLOW" and inner_decision["verdict"] == "WARN":
                verdict = {"verdict": "WARN", "risk_score": risk_score, "requires_confirmation": True}

        latency_ms = (time.perf_counter() - start) * 1000
        return self._build_output(
            original, expanded, rule_matches, ml_result, llm_explanation, risk_score, verdict, latency_ms
        )

    def _unwrap_payload(self, command):
        """Return the quoted payload of `bash -c '...'`/`sh -c "..."`, or None."""
        m = WRAPPER_RE.match(command)
        return m.group(2) if m else None

    def _classify(self, normalized, features):
        if self.model is None or self.vectorizer is None:
            return {
                "predicted_label": self.config["model"]["fallback_label"],
                "confidence": 0.0,
                "probabilities": {},
                "top_features": [],
            }
        try:
            import numpy as np
            vector = np.array(feature_vector(features)).reshape(1, -1)
            vector = self.vectorizer.transform(vector)
            probs = self.model.predict_proba(vector)[0]
            label = self.model.predict(vector)[0]
            confidence = float(max(probs))
            probabilities = {
                str(cls): float(prob)
                for cls, prob in zip(self.model.classes_, probs)
            }
            importances = np.asarray(self.model.feature_importances_)
            values = np.asarray(feature_vector(features), dtype=float)
            contrib = importances * values
            top_idx = np.argsort(-contrib)
            top_features = [
                FEATURE_NAMES[i] for i in top_idx if values[i] > 0
            ][:5]
            return {
                "predicted_label": label,
                "confidence": confidence,
                "probabilities": probabilities,
                "top_features": top_features,
            }
        except Exception:
            return {
                "predicted_label": self.config["model"]["fallback_label"],
                "confidence": 0.0,
                "probabilities": {},
                "top_features": [],
            }

    def _explain(self, original, normalized, rule_matches, ml_result, features):
        result = {"model": None, "summary": None, "suggested_alternative": None}
        if self.llm is None:
            return result
        if rule_matches:
            rule = rule_matches[0]
            return {
                "model": "rule",
                "summary": rule["explanation"],
                "suggested_alternative": rule.get("alternative"),
            }
        if features.get("whitelist_match"):
            return {
                "model": "whitelist",
                "summary": "This command matches a known-safe whitelist pattern.",
                "suggested_alternative": None,
            }
        llm_cfg = self.config["llm"]
        ambiguous = ml_result.get("confidence", 0) < llm_cfg.get("ambiguity_threshold", 0.65)
        use_for_ambiguous = llm_cfg.get("use_for_ambiguous_only", True)
        if use_for_ambiguous and not ambiguous:
            return result
        if not self.llm.is_available():
            return result
        try:
            explanation = self.llm.explain(original, rule_matches)
            return {
                "model": llm_cfg.get("model"),
                "summary": explanation.get("summary"),
                "suggested_alternative": explanation.get("alternative"),
            }
        except Exception:
            return result

    def _blend_risk(self, rule_score, ml_result):
        label = ml_result.get("predicted_label", "safe")
        confidence = ml_result.get("confidence", 0.0)
        label_risk = {"destructive": 95, "risky": 70, "safe": 15}.get(label, 15)
        if rule_score == 0:
            return min(100, round(label_risk * (0.4 + 0.6 * min(1.0, confidence))))
        ml_weight = 0.35 if confidence > 0.6 else 0.15
        blended = rule_score * (1 - ml_weight) + label_risk * ml_weight
        # a matched rule always counts: never let ML confidence dilute a rule match
        # below the rule's own severity weight (prevents low rules from ALLOWing).
        return min(100, max(rule_score, round(blended)))

    def _decide(self, risk_score, rule_matches, ml_result):
        cfg = self.config["engine"]
        critical_rule = any(m["severity"] == "critical" for m in rule_matches)
        destructive_ml = ml_result.get("predicted_label") == "destructive"
        if critical_rule or destructive_ml and ml_result.get("confidence", 0) >= cfg.get("ml_block_confidence", 0.8) or risk_score >= cfg["block_risk_score"]:
            verdict = "BLOCK"
        elif risk_score >= cfg["warn_risk_score"]:
            verdict = "WARN"
        else:
            verdict = "ALLOW"
        requires_confirmation = verdict in ("BLOCK", "WARN")
        return {"verdict": verdict, "risk_score": risk_score, "requires_confirmation": requires_confirmation}

    def _build_output(self, original, expanded, rule_matches, ml_result, llm_explanation, risk_score, verdict, latency_ms):
        return {
            "command": original,
            "expanded_command": expanded,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_engine": {
                "matched": bool(rule_matches),
                "rules": rule_matches,
            },
            "ml_classifier": ml_result,
            "llm_explanation": llm_explanation,
            "sandbox_check": {"enabled": False, "result": None},
            "final_decision": {
                "verdict": verdict["verdict"],
                "risk_score": verdict["risk_score"],
                "requires_confirmation": verdict["requires_confirmation"],
                "latency_ms": round(latency_ms, 1),
            },
        }

    def audit(self, result):
        cfg = self.config["engine"]
        log_path = os.path.expanduser(cfg.get("log_path", "~/.csengine/audit.log"))
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        hashed_only = cfg.get("audit_hashed_only", True)
        entry = {
            "timestamp": result["timestamp"],
            "verdict": result["final_decision"]["verdict"],
            "risk_score": result["final_decision"]["risk_score"],
            "command_hash": hashlib.sha256(result["command"].encode()).hexdigest()[:16] if hashed_only else result["command"],
            "rule_ids": [r["rule_id"] for r in result["rule_engine"]["rules"]],
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return log_path
