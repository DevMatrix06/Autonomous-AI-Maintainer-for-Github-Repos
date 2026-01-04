from tools.static import run_static_analysis

def analyse_repo(repo_path):
    issues = run_static_analysis(repo_path)
    return issues
