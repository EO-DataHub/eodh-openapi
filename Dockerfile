# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim@sha256:d1e005e6f5aac724b7554db95f1c128a77d8d35b59ebe70e188852b4bdad3a3d

ENV UV_NO_DEV=1

WORKDIR /app

# Put the project venv first on PATH so `python -m eodh_openapi` works without `uv run`
# (the ArgoCD deployment overrides the entrypoint with a bare `python` command).
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy project files
COPY . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

EXPOSE 8000
ENTRYPOINT ["uv", "run", "--no-sync", "python", "-m", "eodh_openapi", "spec", "serve", "--port=8000"]
