FROM python:3.13-slim

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update -y && apt-get upgrade -y

WORKDIR /app

ADD LICENSE requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt

ADD eodh_openapi eodh_openapi
ADD pyproject.toml ./

EXPOSE 8000
ENTRYPOINT ["python", "-m", "eodh_openapi", "spec", "serve", "--port=8000"]
