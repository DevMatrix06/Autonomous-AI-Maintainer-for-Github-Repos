# Build:
#   docker build -f docker/sandbox.dockerfile -t ai-agent .
#
# Run:
#   docker run --rm \
#     -e GITHUB_TOKEN=ghp_your_token_here \
#     -e ANTHROPIC_API_KEY=sk-ant-... \
#     -e AUTO_CONFIRM=1 \
#     ai-agent python main.py https://github.com/owner/repo

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /agent

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
