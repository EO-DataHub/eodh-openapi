import json
import logging
import os.path
from dataclasses import dataclass, field
from typing import Any

import click
import yaml

from . import utils
from .log import logger


@dataclass
class Config:
    @dataclass
    class APISource:
        url: str
        prefix: str = ""

    base_url: str
    merge_keys: list[str] = field(default_factory=list)
    sources: list[APISource] = field(default_factory=list)

    @staticmethod
    def load(filename: str) -> "Config":
        try:
            with open(filename, "r") as f:
                config_data: dict = yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Config file {filename} not found.")
            raise

        return Config(
            base_url=config_data["base_url"],
            merge_keys=config_data.get("merge_keys", []),
            sources=[
                Config.APISource(url=source["url"], prefix=source.get("prefix", ""))
                for source in config_data.get("sources", [])
            ],
        )


@click.group()
def cli():
    pass


@cli.group()
def spec():
    pass


@spec.command()
@click.option(
    "-c",
    "--config",
    "config_file",
    default="config.yaml",
    help="Path to the config file",
    show_default=True,
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default="openapi.yaml",
    help="Output filename",
    show_default=True,
)
def merge(config_file: str, output_file: str):
    """
    Merge OpenAPI specs from multiple sources into a single spec.
    """
    config = Config.load(config_file)
    logger.info(f"Loaded config from {config_file}")

    # Load base OpenAPI spec
    try:
        spec = utils.load_spec(config.base_url)
    except Exception as e:
        logger.error(f"Failed to load base OpenAPI spec: {e}")
        raise
    else:
        logger.info(f"Loaded base OpenAPI spec from {config.base_url}")

    # Merge all sources into the OpenAPI spec
    for source in config.sources:
        try:
            other = utils.load_spec(source.url)
        except Exception as e:
            logger.error(f"Failed to load spec from {source.url}: {e}. Skipping.")
            continue
        else:
            logger.info(f"Merging spec from {source.url} into base spec.")

        # Overwrite existing paths in other with paths with source prefix
        paths: dict[str, Any] = other.setdefault("paths", {})
        new_paths: dict[str, Any] = {}
        for k, v in paths.items():
            new_paths[f"{source.prefix}{k}"] = v
        other["paths"] = new_paths

        # Merge specified keys of the OpenAPI spec
        for key in config.merge_keys:
            logger.info(f"Merging key: {key}")
            d1: dict = spec
            d2: dict = other
            for subkey in key.split("."):
                d1 = d1.setdefault(subkey, {})
                d2 = d2.setdefault(subkey, {})

            utils.recursive_merge(d1, d2, key)

    _, ext = os.path.splitext(output_file)
    with open(output_file, "w") as f:
        if ext in (".yaml", ".yml"):
            yaml.dump(spec, f, sort_keys=False)
        else:
            json.dump(spec, f, indent=2)


if __name__ == "__main__":
    cli(obj={})
