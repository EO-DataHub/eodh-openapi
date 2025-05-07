import json
import logging
import os.path
from dataclasses import dataclass, field
from typing import Any, TypedDict

import click
import uvicorn
import yaml

from . import utils, web
from .log import logger


@dataclass
class Config:
    @dataclass
    class APISource:
        class Server(TypedDict):
            url: str
            description: str

        url: str
        prefix: str = ""
        servers: list[Server] = field(default_factory=list)
        tags: list[str] = field(default_factory=list)
        description_overrides: dict[str, str] = field(default_factory=dict)

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
                Config.APISource(
                    url=source["url"],
                    prefix=source.get("prefix", ""),
                    servers=source.get("servers", []),
                    tags=source.get("tags", []),
                    description_overrides=source.get("description_overrides", {}),
                )
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
def generate(config_file: str, output_file: str):
    """
    Generate OpenAPI spec from multiple sources into a single spec.
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
            new_paths[f"{source.prefix}{k}"].setdefault("servers", []).extend(
                source.servers
            )  # Add source servers to the paths, if any
            for method, op in v.items():
                if not isinstance(op, dict):
                    continue
                op["tags"] = source.tags

            # apply per-path description overrides
            for path_suffix, desc in source.description_overrides.items():
                full_path = f"{source.prefix}{path_suffix}"
                if full_path in new_paths:
                    for op in new_paths[full_path].values():
                        if isinstance(op, dict):
                            op["description"] = desc
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


@spec.command()
@click.option("--title", "title", default="OpenAPI Spec", help="Title of the app")
@click.option(
    "--spec", "spec_file", default="openapi.json", help="Path to the OpenAPI spec"
)
@click.option("-h", "--host", "host", default="0.0.0.0", help="Host to serve app on")
@click.option("-p", "--port", "port", default=8000, help="Port to serve app on")
@click.option("--base-path", "base_path", default="", help="Base path to serve the app")
@click.option(
    "--static-dir",
    "static_dir",
    default=None,
    help="Path to the static files directory",
)
@click.option("--log-level", "log_level", default="info", help="Log level of the app")
def serve(
    title: str,
    spec_file: str,
    host: str,
    port: int,
    base_path: str,
    static_dir: str,
    log_level: str,
):
    """
    Serve the OpenAPI spec as a FastAPI app.
    """
    app = web.create_app(
        title=title,
        base_path=base_path,
        static_dir=static_dir,
        openapi_spec=spec_file,
    )
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
    )


if __name__ == "__main__":
    cli(obj={})
