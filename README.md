[![lint-and-smoke](https://github.com/DevMatrix06/Autonomous-AI-Maintainter-for-Github-Repos/actions/workflows/ci.yml/badge.svg)](https://github.com/DevMatrix06/Autonomous-AI-Maintainter-for-Github-Repos/actions/workflows/ci.yml)

# AI Agent — Automated Python Repo Maintainer

An autonomous agent that clones a GitHub repository, detects Python syntax and static errors, fixes them using an LLM (with a deterministic fallback), runs the test suite, then commits the fixes and opens a pull request.

## How it works

1. **Clone** — clones the target repo into a temp directory.
2. **Branch** — creates a timestamped branch `ai-maintainer-fixes-<epoch>`.
3. **Analyse** — runs `py_compile` (syntax errors) and `pylint --errors-only` (static errors) across all Python files, skipping `__pycache__`, `.venv`, and `.git`.
4. **Fix** — for each issue:
   - **LLM path (primary):** sends the file source and error details to Groq (`llama-3.3-70b-versatile`) using `prompts/fix-code.txt`. Validates the response compiles before accepting it.
   - **Deterministic fallback:** if the LLM is unavailable or its output doesn't compile, and the error is a `SYNTAX_ERROR`, iteratively removes the offending line until the file compiles.
   - Shows a unified diff of all proposed changes and asks for confirmation before writing anything to disk.
5. **Test** — runs `pytest` in the repo root (120 s timeout).
6. **Commit & Push** — stages only modified `.py` files, commits, and pushes the branch.
7. **PR** — creates a GitHub pull request against the repo's default branch (or returns the URL of an existing open PR for the same branch).

The loop runs up to `MAX_ITERATIONS = 5` times, re-analysing after each fix, so multiple errors across files are resolved in successive iterations.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```
GITHUB_TOKEN=ghp_...        # GitHub PAT with repo + pull_request scopes
GROQ_API_KEY=your_key_here  # Required for the LLM fix path — free tier at console.groq.com
AUTO_CONFIRM=0               # Set to 1 to skip the y/n diff prompt (CI/unattended)
SKIP_MISSING_PYTEST=0        # Set to 1 if the target repo has no test suite
```

Load the file before running (e.g. `export $(cat .env | xargs)` on Linux/macOS, or use `python-dotenv`).

## Usage

```bash
python main.py https://github.com/owner/repo
```

**HTTPS URLs only.** SSH remotes (`git@github.com:…`) are rejected with a clear error because token injection into SSH URLs is not supported.

## Docker

```bash
# Build
docker build -f docker/sandbox.dockerfile -t ai-agent .

# Run
docker run --rm \
  -e GITHUB_TOKEN=ghp_your_token_here \
  -e GROQ_API_KEY=your_key_here \
  -e AUTO_CONFIRM=1 \
  ai-agent python main.py https://github.com/owner/repo
```

## Limitations

- **HTTPS remotes only** — SSH URLs are not supported for push/PR creation.
- **Interactive confirmation by default** — set `AUTO_CONFIRM=1` for unattended runs.
- **LLM fallback behaviour** — if `GROQ_API_KEY` is unset or the API call fails, only `SYNTAX_ERROR` issues can be fixed (via line removal). `PYLINT_ERROR` issues are skipped when the LLM is unavailable.
- **Line-removal fallback is lossy** — the deterministic fallback deletes the error line, which is a last resort. The LLM path produces semantically correct fixes.
- **No sandboxing** — the agent runs tests directly on the cloned repo. Use the Docker image to isolate execution.
