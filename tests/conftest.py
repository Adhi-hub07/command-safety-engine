import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import CommandSafetyEngine


class _StubLLM:
    """Fast, deterministic stand-in for the live Ollama model in unit tests."""

    def is_available(self):
        return False

    def explain(self, command, rule_matches=None, decoded_payload=None):
        return {"summary": "stub", "alternative": "stub", "risk": "safe"}

    def undo_plan(self, command):
        return []


@pytest.fixture(autouse=True)
def stub_llm(monkeypatch):
    """Keep the test suite hermetic and fast: never hit the live Ollama server.

    The dedicated LLM-path tests inject their own controllable fake via
    ``engine.llm``, so they are unaffected by this autouse fixture.
    """
    monkeypatch.setattr(CommandSafetyEngine, "_load_llm", lambda self: setattr(self, "llm", _StubLLM()))