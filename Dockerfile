# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim@sha256:331fbb158258608b9391e802305a9a2c9e42d689435c1d98706647122a122ab0

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
