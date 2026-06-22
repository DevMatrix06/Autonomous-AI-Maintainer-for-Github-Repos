"""
Smoke test: analyser detects a syntax error, fixer resolves it (deterministic
fallback path — no ANTHROPIC_API_KEY required).
"""
import os
import tempfile
from pathlib import Path

import pytest

from tools.static import run_static_analysis
from agents.fixer import fix_issues


BROKEN_SOURCE = "def greet(name)\n    return f'Hello, {name}'\n"


@pytest.fixture()
def broken_repo(tmp_path):
    """A minimal repo directory containing one Python file with a syntax error."""
    (tmp_path / "broken.py").write_text(BROKEN_SOURCE, encoding="utf-8")
    return tmp_path


def test_analyser_detects_syntax_error(broken_repo):
    issues = run_static_analysis(str(broken_repo))
    assert len(issues) >= 1
    types = [i["type"] for i in issues]
    assert "SYNTAX_ERROR" in types


def test_fixer_produces_compilable_output(broken_repo, monkeypatch):
    # Force the deterministic fallback by ensuring no API key is present,
    # and auto-approve the diff so no stdin is needed.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTO_CONFIRM", "1")

    issues = run_static_analysis(str(broken_repo))
    assert issues, "Precondition: analyser must find at least one issue"

    result = fix_issues(str(broken_repo), issues)
    assert result is True, "fix_issues should return True when a fix was applied"

    fixed_path = broken_repo / "broken.py"
    fixed_source = fixed_path.read_text(encoding="utf-8")

    # Validate the fixed file compiles
    try:
        compile(fixed_source, str(fixed_path), "exec")
    except SyntaxError as exc:
        pytest.fail(f"Fixed file still has a syntax error: {exc}")
