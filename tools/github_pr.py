import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def create_pull_request(repo_url, title, body, branch="ai-maintainer-fixes"):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")

    owner, repo = repo_url.rstrip("/").split("/")[-2:]

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 1️⃣ Check if PR already exists
    check_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {
        "head": f"{owner}:{branch}",
        "base": "main",
        "state": "open"
    }

    r = requests.get(check_url, headers=headers, params=params)
    r.raise_for_status()

    existing = r.json()
    if existing:
        return existing[0]["html_url"]

    # 2️⃣ Create PR if none exists
    create_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    payload = {
        "title": title,
        "body": body,
        "head": branch,
        "base": "main"
    }

    r = requests.post(create_url, json=payload, headers=headers)
    r.raise_for_status()

    return r.json()["html_url"]
