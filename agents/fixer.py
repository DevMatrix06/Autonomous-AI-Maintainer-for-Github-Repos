import os
import difflib
import subprocess
import tempfile
from pathlib import Path

from tools.logger import info, debug


_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _get_syntax_error_line(source: str, file_path: str):
    try:
        compile(source, file_path, "exec")
        return None
    except SyntaxError as e:
        return e.lineno


def _remove_line(source: str, line_no: int):
    lines = source.splitlines(keepends=True)
    if not line_no or line_no <= 0 or line_no > len(lines):
        return None
    debug(f"Removing line {line_no}: {lines[line_no - 1].rstrip()}")
    del lines[line_no - 1]
    return "".join(lines)


def _fix_source(source: str, file_path: str):
    """
    Iteratively remove syntax-error lines in memory until the source compiles
    or no further progress is possible. Returns fixed source, or None.
    """
    current = source
    while True:
        error_line = _get_syntax_error_line(current, file_path)
        if error_line is None:
            return current
        fixed = _remove_line(current, error_line)
        if fixed is None or fixed == current:
            return None
        current = fixed


def _try_llm_fix(file_path: str, source: str, issue: dict):
    """
    Ask the LLM to fix the reported issue. Validates that the returned
    candidate compiles before accepting it. Returns fixed source string on
    success, None on any failure (missing API key, network error, compile
    failure).
    """
    try:
        from tools.llm import call_llm

        template = (_PROMPTS_DIR / "fix-code.txt").read_text(encoding="utf-8")
        error_message = issue.get("details") or issue.get("message") or ""

        prompt = template.format(
            file_path=file_path,
            source_code=source,
            error_type=issue.get("type", ""),
            error_message=error_message,
        )

        candidate = call_llm(prompt)

        # Write candidate to a temp file and py_compile it to validate
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(candidate)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", tmp_path],
                capture_output=True
            )
            if result.returncode != 0:
                debug(f"LLM candidate for {os.path.basename(file_path)} does not compile")
                return None
        finally:
            os.unlink(tmp_path)

        return candidate

    except Exception as e:
        info(f"LLM fix failed for {os.path.basename(file_path)}: {e}")
        return None


def fix_issues(_repo_path, issues):
    """
    Propose fixes for all issues, show a unified diff, then write to disk only
    after user confirmation (or AUTO_CONFIRM=1). Returns True if at least one
    fix was written, False otherwise.

    Fix strategy per file (LLM-first with deterministic fallback):
      1. Try LLM using prompts/fix-code.txt; accept if candidate compiles.
      2. If LLM fails and issue type is SYNTAX_ERROR: fall back to line-removal.
      3. If both fail: skip the file with a warning.
    """
    if not issues:
        info("No issues to fix")
        return False

    # One primary issue per file (first occurrence wins)
    files_to_fix = {}
    for issue in issues:
        fp = issue["file"]
        if fp not in files_to_fix:
            files_to_fix[fp] = issue

    proposals = []  # list of (file_path, original_source, fixed_source)

    for file_path, issue in files_to_fix.items():
        path = Path(file_path)
        try:
            original = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            info(f"Cannot read {file_path}: {e}")
            continue

        fixed = _try_llm_fix(file_path, original, issue)

        if fixed is None:
            if issue.get("type") == "SYNTAX_ERROR":
                info(f"LLM fix failed, falling back to line removal for {os.path.basename(file_path)}")
                fixed = _fix_source(original, file_path)
            # PYLINT_ERROR with no working LLM fix → no deterministic fallback

        if fixed is None:
            info(f"Could not fix {file_path} — skipping")
            continue

        if fixed == original:
            debug(f"No change needed for {file_path}")
            continue

        proposals.append((file_path, original, fixed))

    if not proposals:
        info("No applicable fix generated")
        return False

    # Print a unified diff for every proposed change
    info("\n--- Proposed changes ---")
    for file_path, original, fixed in proposals:
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"a/{os.path.basename(file_path)}",
            tofile=f"b/{os.path.basename(file_path)}",
        )
        info("".join(diff))

    # AUTO_CONFIRM=1 skips the interactive prompt for unattended/CI runs
    if os.getenv("AUTO_CONFIRM") == "1":
        info("AUTO_CONFIRM=1 — auto-approving fixes")
        confirmed = True
    else:
        print("Apply these fixes? (y/n): ", end="", flush=True)
        confirmed = input().strip().lower() == "y"

    if not confirmed:
        info("Fix skipped by user")
        return False

    for file_path, _, fixed in proposals:
        Path(file_path).write_text(fixed, encoding="utf-8")
        info(f"Fixed: {file_path}")

    info(f"{len(proposals)} file(s) fixed")
    return True
