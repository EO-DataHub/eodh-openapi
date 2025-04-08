import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

import click
import requests
import yaml

from . import OpenAPISpec

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    handlers=[logging.StreamHandler()],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

HTTP_PATTERN = re.compile(r"^(http|https)://", re.IGNORECASE)
FILE_PATTERN = re.compile(r"^(file)://", re.IGNORECASE)


@dataclass
class APISource:
    name: str
    prefix: str
    url: str


@dataclass
class Config:
    title: str
    version: str
    openapi_version: str
    docs_url: str
    openapi_url: str
    description: str = None
    tags: list[dict[str, Any]] = field(default_factory=list)
    sources: list[APISource] = field(default_factory=list)

    @staticmethod
    def load(filename: str) -> "Config":
        try:
            with open(filename, "r") as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Config file {filename} not found.")
            raise

        return Config(
            title=config_data["title"],
            version=config_data["version"],
            openapi_version=config_data.get("openapi_version", "3.1.0"),
            docs_url=config_data.get("docs_url", "/docs"),
            openapi_url=config_data.get("openapi_url", "/docs/openapi.json"),
            sources=[
                APISource(name=entry["name"], prefix=entry["prefix"], url=entry["url"])
                for entry in config_data.get("sources", [])
            ],
        )


@click.group()
@click.option("--config", default="config.yaml", help="Path to the config file.")
@click.pass_context
def cli(ctx, config: str):
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.load(config)


@cli.command()
@click.pass_context
def merge(ctx):
    config: Config = ctx.obj["config"]

    # Initialise the OpenAPI spec object from the input config file
    spec = OpenAPISpec(
        openapi=config.openapi_version,
        info=OpenAPISpec.Info(
            title=config.title,
            version=config.version,
            description=config.description,
        ),
        tags=config.tags,
    )

    # Merge all sources into the OpenAPI spec
    for source in config.sources:
        match source:
            case _ if HTTP_PATTERN.match(source.url):
                spec_data = fetch_http_spec(source.url)
            case _ if FILE_PATTERN.match(source.url):
                spec_data = load_file_spec(source.url)
            case _:
                logger.warning(f"Unknown source type for {source.url}. Skipping.")
                continue

        other_spec = OpenAPISpec(**spec_data)
        spec.merge(spec_data, other_spec)


def fetch_http_spec(url: str) -> OpenAPISpec:
    """Fetch OpenAPI spec from a given HTTP[S] URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        raise
    else:
        return response.json()


def load_file_spec(url: str) -> OpenAPISpec:
    """Load OpenAPI spec from a local file."""
    try:
        with open(url, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Failed to load {url}: {e}")
        raise


if __name__ == "__main__":
    cli(obj={})
