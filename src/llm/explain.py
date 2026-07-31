"""Local offline LLM explanation layer via Ollama (Qwen 2.5 3B)."""

import json
import re

SYSTEM_PROMPT = """You are a Linux command safety analyst. Given a shell command, decide its risk level and explain in one short paragraph. Always return STRICT JSON only, with exactly these keys:
{"risk": "safe"|"risky"|"destructive", "summary": "...", "alternative": "..."}
Never explain yourself outside the JSON. Keep summary under 40 words."""


class LLMExplainer:
    def __init__(self, model="qwen2.5:3b-instruct-q4_K_M", base_url="http://localhost:11434", timeout_seconds=4):
        self.model = model
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self._client = None
        self._available = None

    def _ensure_client(self):
        """Import ollama lazily so a missing install costs ~0ms at load time."""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.base_url, timeout=self.timeout_seconds)
            except ImportError:
                self._client = False
        return self._client

    def is_available(self):
        """Return True if the local Ollama server responds. Cached per process.

        Uses a raw TCP socket probe (0.5s timeout) so a downed server is
        detected in milliseconds instead of a full HTTP timeout.
        """
        if self._available is None:
            try:
                import socket
                from urllib.parse import urlparse

                parsed = urlparse(self.base_url if "://" in self.base_url else "http://" + self.base_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 11434
                sock = socket.create_connection((host, port), timeout=0.5)
                sock.close()
                self._available = self._ensure_client() is not False
            except Exception:
                self._available = False
        return self._available

    def explain(self, command, rule_matches=None):
        """Return {"summary": ..., "alternative": ...} or raise on failure."""
        client = self._ensure_client()
        if not client:
            raise RuntimeError("ollama python client not installed")
        context = ""
        if rule_matches:
            ids = ", ".join(m["rule_id"] for m in rule_matches)
            context = f" A rule engine already flagged this as matching: {ids}."
        user_msg = f"Command: {command}\n{context}\nReturn JSON."
        response = client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            format="json",
        )
        content = response.get("message", {}).get("content", "")
        return self._parse(content)

    @staticmethod
    def _parse(content):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            data = json.loads(match.group(0)) if match else {}
        return {
            "summary": data.get("summary", ""),
            "alternative": data.get("alternative", ""),
            "risk": data.get("risk", ""),
        }
