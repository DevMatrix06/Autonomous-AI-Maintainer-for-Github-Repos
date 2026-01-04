import sys
from agents.controller import run_pipeline

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <github_repo_url>")
        sys.exit(1)

    repo_url = sys.argv[1]
    run_pipeline(repo_url)
