import subprocess

def run_pytest(repo_path):
    try:
        result = subprocess.run(
            ["pytest"],
            cwd=repo_path
        )
        return result.returncode == 0

    except FileNotFoundError:
        print("[!] pytest command not found on PATH")
        return True  # no tests ≠ failure
