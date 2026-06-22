import os
import subprocess

from tools.logger import info


def run_pytest(repo_path):
    try:
        result = subprocess.run(
            ["pytest"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.stdout:
            info(result.stdout)
        if result.stderr:
            info(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        info("[!] pytest timed out after 120 seconds")
        return False

    except FileNotFoundError:
        # SKIP_MISSING_PYTEST=1 opts into "no pytest = pass" for repos with no tests
        if os.getenv("SKIP_MISSING_PYTEST") == "1":
            info("[!] pytest not found on PATH — skipping test validation (SKIP_MISSING_PYTEST=1)")
            return True
        info("[!] pytest not found on PATH — treating as test failure")
        return False
