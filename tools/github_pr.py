import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def parse_repo_url(url):
    """
    Return (owner, repo_name) from either:
      HTTPS — https://github.com/owner/repo[.git]
      SSH   — git@github.com:owner/repo[.git]
    Raises ValueError for unrecognised formats.
    """
    url = url.rstrip("/")
    if url.startswith("https://") or url.startswith("http://"):
        parts = url.split("/")
        if len(parts) < 2:
            raise ValueError(f"Cannot parse HTTPS repo URL: {url!r}")
        owner = parts[-2]
        repo_name = parts[-1].removesuffix(".git")
    elif url.startswith("git@"):
        # git@github.com:owner/repo.git
        try:
            _, path = url.split(":", 1)
            owner, repo_name = path.split("/", 1)
            repo_name = repo_name.removesuffix(".git")
        except ValueError:
            raise ValueError(f"Cannot parse SSH repo URL: {url!r}")
    else:
        raise ValueError(f"Unrecognised repo URL format: {url!r}")
    return owner, repo_name


def get_default_branch(owner, repo, headers):
    """Return the default branch name for the given repo."""
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=headers
    )
    r.raise_for_status()
    return r.json()["default_branch"]


def create_pull_request(repo_url, title, body, branch):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")

    owner, repo = parse_repo_url(repo_url)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    default_branch = get_default_branch(owner, repo, headers)

    # 1. Check if PR already exists
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        params={"head": f"{owner}:{branch}", "base": default_branch, "state": "open"}
    )
    r.raise_for_status()

    existing = r.json()
    if existing:
        return existing[0]["html_url"]

    # 2. Create PR if none exists
    r = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        json={"title": title, "body": body, "head": branch, "base": default_branch},
        headers=headers
    )
    r.raise_for_status()

    return r.json()["html_url"]
