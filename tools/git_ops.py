import subprocess
import os
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def create_branch(repo_path):
    branch_name = f"ai-maintainer-fixes-{int(time.time())}"
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=repo_path,
        check=True
    )
    return branch_name


def commit_changes(repo_path, message="AI: automated fix"):
    # Collect modified tracked files and any .py files with changes
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True
    )
    changed_files = [f for f in result.stdout.splitlines() if f.endswith(".py")]

    if changed_files:
        subprocess.run(["git", "add", "--"] + changed_files, cwd=repo_path, check=True)

    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        check=True
    )


def push_branch(repo_path, repo_url, branch_name):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")

    if repo_url.startswith("git@"):
        raise RuntimeError(
            "SSH remote URLs require manual push credentials. "
            "Use an HTTPS remote URL with GITHUB_TOKEN instead."
        )

    # Inject token into HTTPS URL
    auth_url = repo_url.replace(
        "https://",
        f"https://{GITHUB_TOKEN}@"
    )

    subprocess.run(
        ["git", "push", auth_url, branch_name],
        cwd=repo_path,
        check=True
    )
