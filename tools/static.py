import re
import subprocess
import os
from pathlib import Path

# pylint error line format: path:line:col: Exxxx: message
_PYLINT_ERROR_RE = re.compile(r"^(.+):(\d+):\d+: E\d+: (.+)$")


def _is_ignored(path: Path):
    return any(
        part in path.parts
        for part in ("__pycache__", ".venv", "venv", ".git")
    ) or path.suffix == ".pyc"


def run_static_analysis(repo_path):
    """
    Static analysis pipeline:
    1. py_compile → real syntax errors
    2. pylint (errors-only, import-error disabled)
    """

    issues = []

    py_files = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            path = Path(root) / f
            if path.suffix == ".py" and not _is_ignored(path):
                py_files.append(str(path))

    for file_path in py_files:

        # 1. PURE SYNTAX CHECK (catches ;;;;)
        syntax = subprocess.run(
            ["python", "-m", "py_compile", file_path],
            capture_output=True,
            text=True
        )

        if syntax.returncode != 0:
            issues.append({
                "type": "SYNTAX_ERROR",
                "file": file_path,
                "details": syntax.stderr.strip()
            })
            continue  # no need to lint broken syntax

        # 2. PYLINT (OPTIONAL, SAFE)
        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pylint",
                    "--errors-only",
                    "--disable=import-error",
                    file_path
                ],
                capture_output=True,
                text=True
            )
            for line in result.stdout.splitlines():
                m = _PYLINT_ERROR_RE.match(line)
                if m:
                    issues.append({
                        "type": "PYLINT_ERROR",
                        "file": os.path.abspath(m.group(1)),
                        "line": int(m.group(2)),
                        "message": m.group(3).strip()
                    })
        except FileNotFoundError:
            # pylint not installed → ignore
            pass

    return issues
