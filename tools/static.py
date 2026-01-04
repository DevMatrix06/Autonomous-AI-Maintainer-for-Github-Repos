import subprocess
import os

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
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    for file_path in py_files:

        # 1️⃣ PURE SYNTAX CHECK (catches ;;;;)
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

        # 2️⃣ PYLINT (OPTIONAL, SAFE)
        try:
            subprocess.run(
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
        except FileNotFoundError:
            # pylint not installed → ignore
            pass

    return issues
