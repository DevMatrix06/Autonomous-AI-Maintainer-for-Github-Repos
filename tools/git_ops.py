import subprocess
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def init_repo(repo_path):
    subprocess.run(["git", "init"], cwd=repo_path, check=True)

def create_branch(repo_path, branch_name="ai-maintainer-fixes"):
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=repo_path,
        check=True
    )

def commit_changes(repo_path, message="AI: automated fix"):
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        check=True
    )

def push_branch(repo_path, repo_url, branch_name="ai-maintainer-fixes"):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")

    # Inject token into HTTPS URL
    auth_url = repo_url.replace(
        "https://",
        f"https://{GITHUB_TOKEN}@"
    )

    subprocess.run(
    ["git", "push", "--force", auth_url, branch_name],
    cwd=repo_path,
    check=True
)

