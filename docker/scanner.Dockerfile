# =============================================================================
# repomend-scanner — custom scanner sandbox image
# =============================================================================
# KS-TRACE: C-P3-08, ADR-013, ADR-014
# | assumption: python:3.12-slim base; iptables + all scanner tools baked in
# | test: test_docker_sandbox.py (integration), AC-P3-01, AC-P3-02
#
# Build:
#   docker build -f docker/scanner.Dockerfile -t repomend-scanner:0.1.0 .
#
# Pin BASE_IMAGE in docker_sandbox.py after build:
#   docker inspect repomend-scanner:0.1.0 --format "{{.Id}}"
#
# Why custom image? (ADR-014)
#   python:3.12-slim does not include iptables. Runtime apt-get install is
#   impossible: egress rules cannot be applied before iptables binary exists,
#   but installing iptables requires network access before rules are set —
#   a chicken-and-egg that makes stock images non-viable for C-P3-08.
#   Scanner binaries baked in at the same time: one image build, not two;
#   pin versions once; reproducible for Phase 4 golden dataset.
# =============================================================================

FROM python:3.12-slim

# ---------------------------------------------------------------------------
# System packages:
#   iptables        — egress enforcement (C-P3-08 / ADR-013)
#   iptables-persistent  — ensures rules survive exec (not strictly needed for
#                    ephemeral containers, but satisfies iptables-save path)
#   curl            — used by AC-P3-02 adversarial IP-block test only
#   git             — required by worktree.py (git version check + operations)
#   nodejs + npm    — ESLint and npm audit (JS repo support)
#                    Version: Node.js 20 LTS (LTS until April 2026, extended to April 2028)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    curl \
    git \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Python scanner tools — pinned at explicit versions (ADR-014 requirement).
#
# VERSIONS BELOW ARE PLACEHOLDERS.
# Replace each ## FILL ## with the confirmed version from:
#   semgrep --version
#   bandit --version
#   pip-audit --version
# before signing the INTAKE contract and pushing the image.
#
# Semgrep:   1.165.0  — confirmed from host (semgrep --version, 2026-06-12)
# Bandit:    1.9.4    — PyPI latest stable (pip index versions bandit, 2026-06-12)
# pip-audit: 2.10.1   — PyPI latest stable (pip index versions pip-audit, 2026-06-12)
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    semgrep==1.165.0 \
    bandit==1.9.4 \
    pip-audit==2.10.1

# ---------------------------------------------------------------------------
# Node scanner tools — pinned at explicit versions (ADR-014 requirement).
#
# ESLint 8.57.1 — intentional: last stable 8.x (pre-flat-config).
# ESLint 9+ requires eslint.config.js; arbitrary repos will not have one.
# ESLint 8.x falls back gracefully on unconfigured repos — correct for a scanner.
# Do not upgrade to 9.x/10.x without adding --no-eslintrc handling in scanner.py.
# ---------------------------------------------------------------------------
RUN npm install -g eslint@8.57.1

# ---------------------------------------------------------------------------
# Entrypoint script — applies iptables egress rules before any scanner exec.
#
# The script is the container entrypoint. It:
#   1. Applies default OUTPUT DROP policy (deny-by-default)
#   2. Resolves destination IPs for the policy passed via
#      PATCHWARD_NETWORK_POLICY (canonical, BACKLOG 16/17) or the legacy
#      REPOMEND_NETWORK_POLICY fallback (see entrypoint.sh)
#   3. Inserts ACCEPT OUTPUT rules for resolved IPs on ports 80/443
#   4. Execs the scanner command (replaces shell process — no wrapper overhead)
#
# Step 3 MUST run before step 2 (resolution needs network; DROP blocks it).
# PATCHWARD_NETWORK_POLICY / REPOMEND_NETWORK_POLICY values: OFFLINE | PYPI_ONLY | NPM_ONLY
# ---------------------------------------------------------------------------
# NOTE (BACKLOG 17, not this pass): the image tag (repomend-scanner:0.1.0
# below) and the installed binary name (repomend-entrypoint) still carry the
# old name. Left untouched here deliberately — they only take effect on the
# next deliberate image rebuild (see docker_sandbox.py's BASE_IMAGE comment),
# so renaming them is bundled with that rebuild, not this internal-identifier
# pass, to avoid mixing a naming cleanup with an image-rebuild decision.
COPY docker/entrypoint.sh /usr/local/bin/repomend-entrypoint
RUN chmod +x /usr/local/bin/repomend-entrypoint

ENTRYPOINT ["/usr/local/bin/repomend-entrypoint"]

# Default working directory for repo mount
WORKDIR /repo
