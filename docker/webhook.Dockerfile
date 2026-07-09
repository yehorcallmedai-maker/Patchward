# =============================================================================
# patchward-webhook — GitHub App + Marketplace webhook receiver
# =============================================================================
# KS-TRACE: P1-WEBHOOK-04
# | assumption: this image runs the FastAPI app in src/patchward/webhook.py
#   behind Fly.io's edge proxy (fly.toml at repo root); it is a SEPARATE
#   image from docker/scanner.Dockerfile, which stays the sandboxed
#   fix-execution environment and is never internet-facing.
#
# Build:
#   docker build -f docker/webhook.Dockerfile -t patchward-webhook:0.1.0 .
#
# Run locally:
#   docker run -p 8000:8000 --env-file .env patchward-webhook:0.1.0
#
# Required environment variables at runtime (set as platform secrets,
# never baked into the image or committed to this repo):
#   GITHUB_APP_ID
#   GITHUB_APP_PRIVATE_KEY        (raw PEM) or GITHUB_APP_PRIVATE_KEY_B64
#   GITHUB_WEBHOOK_SECRET
#   ANTHROPIC_API_KEY
# =============================================================================

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN pip install --no-cache-dir uv \
    && uv pip install --system --no-cache .[webhook]

# Scanner tools (semgrep/bandit/pip-audit) are intentionally NOT installed
# here — this image only receives webhooks and dispatches clone+pipeline
# work; it shells out to the same run_repo_pipeline code path the CLI
# uses, which expects those tools on PATH inside whatever environment
# actually runs the scan. For v0, install them in this same image too
# (simplest, one deploy target) rather than split into a second worker
# image — revisit if webhook latency or image size becomes a problem.
RUN pip install --no-cache-dir semgrep bandit pip-audit

EXPOSE 8000

CMD ["uvicorn", "patchward.webhook:app", "--host", "0.0.0.0", "--port", "8000"]
