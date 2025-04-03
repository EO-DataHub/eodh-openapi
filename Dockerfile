# syntax=docker/dockerfile:1
FROM python:3.11-slim-bullseye

# Optimize package caching
RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update -y && apt-get upgrade -y

# Set working directory inside the container
WORKDIR /app

# Install dependencies
ADD LICENSE requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt

# Copy necessary files
ADD main.py ./
ADD pyproject.toml ./

# Run the application
EXPOSE 8000
ENTRYPOINT ["fastapi", "run", "main.py", "--port=8000"]

