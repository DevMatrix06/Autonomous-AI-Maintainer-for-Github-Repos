import os
from pathlib import Path


def _is_ignored(path: Path):
    return any(
        part in path.parts
        for part in ("__pycache__", ".venv", "venv", ".git")
    ) or path.suffix == ".pyc"


def _find_python_files(repo_path):
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                if not _is_ignored(path):
                    yield path


def _get_syntax_error_line(file_path):
    try:
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        compile(source, str(file_path), "exec")
        return None
    except SyntaxError as e:
        return e.lineno


def _remove_line(file_path, line_no):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if not line_no or line_no <= 0 or line_no > len(lines):
        return False

    print(f"[i] Removing line {line_no}: {lines[line_no - 1].strip()}")
    del lines[line_no - 1]

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True


def fix_issues(repo_path, issues):
    """
    Fix ALL syntax errors in the repo.
    Returns True if any fix was applied, else False.
    """

    any_fix_applied = False

    for py_file in _find_python_files(repo_path):
        while True:
            error_line = _get_syntax_error_line(py_file)
            if not error_line:
                break  # file is clean

            print(f"\nTrying to fix SYNTAX_ERROR in {py_file}")
            applied = _remove_line(py_file, error_line)
            if not applied:
                break

            any_fix_applied = True

    if not any_fix_applied:
        print("[i] No applicable fix generated")
        return False

    print("\nApply these syntax fixes? (y/n): ", end="")
    choice = input().strip().lower()

    if choice != "y":
        print("[i] Fix skipped by user")
        return False

    print("[✓] Syntax errors removed")
    return True
