"""
Shared pytest configuration for RepoMend test suite.

Loads .env at collection time so ANTHROPIC_API_KEY, GITHUB_TOKEN,
LANGFUSE_PUBLIC_KEY, and LANGFUSE_SECRET_KEY are available to
integration tests without manual $env:VAR = "..." setup.
python-dotenv is already a dev dependency (AC-P1-10).
"""
from dotenv import load_dotenv

load_dotenv()
