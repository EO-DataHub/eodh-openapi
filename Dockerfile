# syntax=docker/dockerfile:1
FROM python:3.11-slim-bullseye

# Optimize package caching
RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update -y && apt-get upgrade -y

# Set working directory inside the container
WORKDIR /hubapi

# Copy necessary files
ADD LICENSE requirements.txt ./
ADD hubapi ./hubapi/
ADD pyproject.toml ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt

# Run the application
CMD ["fastapi", "run", "hubapi/app.py"]

