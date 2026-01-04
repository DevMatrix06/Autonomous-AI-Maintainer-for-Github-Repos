from agents.analyser import analyse_repo
from agents.fixer import fix_issues
from agents.tester import run_tests
from tools.git import clone_repo
from tools.git_ops import init_repo, create_branch, commit_changes, push_branch
from tools.github_pr import create_pull_request
from tools.logger import info, debug
import os
MAX_ITERATIONS = 5

def run_pipeline(repo_url):
    repo_path = clone_repo(repo_url)
    init_repo(repo_path)
    create_branch(repo_path)

    for iteration in range(1, MAX_ITERATIONS + 1):
        info(f"\nIteration {iteration}")

        issues = analyse_repo(repo_path)

        if not issues:
            info("Issue detected: None")
            info("Repository is clean")
            info("No Pull Request created")
            return

        issue = issues[0]
        info(f"Issue detected: {issue['type']}")
        info(f"Issue detected: {issue['type']} in {os.path.basename(issue['file'])}")


        info("Attempting automated fix...")
        applied = fix_issues(repo_path, issues)

        if not applied:
            info("Fix skipped or not applicable")
            info("No Pull Request created")
            return

        commit_changes(repo_path)

        if not run_tests(repo_path):
            info("Tests failed")
            info("No Pull Request created")
            return

        push_branch(repo_path, repo_url)
        pr_url = create_pull_request(
            repo_url,
            title="AI Maintainer: Automated Fix",
            body="Automated fix approved by human reviewer."
        )

        info("Fix applied successfully")
        info(f"Pull Request created: {pr_url}")
        return
