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
        filters: dict[str, list[str]] = field(default_factory=dict)

    class TagDefinition(TypedDict):
        name: str
        description: str = ""

    base_url: str
    merge_keys: list[str] = field(default_factory=list)
    sources: list[APISource] = field(default_factory=list)
    tags: list[TagDefinition] = field(default_factory=list)

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
                    filters=source.get("filters", {}),
                )
                for source in config_data.get("sources", [])
            ],
            tags=[
                Config.TagDefinition(
                    name=tag["name"], description=tag.get("description", "")
                )
                for tag in config_data.get("tags", [])
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

    # Set the tags for the base spec
    spec.setdefault("tags", [])
    for tag in config.tags:
        spec["tags"].append(tag)

    # Merge all sources into the OpenAPI spec
    for source in config.sources:
        try:
            other = utils.load_spec(source.url)
        except Exception as e:
            logger.error(f"Failed to load spec from {source.url}: {e}. Skipping.")
            continue
        else:
            logger.info(f"Merging spec from {source.url} into base spec.")

        # If we are not overwriting tags for this source then add original spec tag definitions
        if not source.tags:
            # copy any top-level tags defined in the fetched spec
            spec.setdefault("tags", []).extend(other.get("tags", []))

        # Overwrite existing paths in other with paths with source prefix
        paths: dict[str, Any] = other.setdefault("paths", {})
        new_paths: dict[str, Any] = {}

        # Precompute the list of tags we should exclude, if any
        filter_tags = source.filters.get("tags", [])
        for path, path_definition in paths.items():
            if filter_tags:
                has_forbidden = False
                for op in path_definition.values():
                    if not isinstance(op, dict):
                        continue
                    # op.get("tags") might be missing or not a list
                    for t in op.get("tags", []):
                        if t in filter_tags:
                            has_forbidden = True
                            break
                    if has_forbidden:
                        break
                if has_forbidden:
                    # skip this entire path
                    continue
            new_paths[f"{source.prefix}{path}"] = path_definition
            new_paths[f"{source.prefix}{path}"].setdefault("servers", []).extend(
                source.servers
            )  # Add source servers to the paths, if any

            if source.tags:
                for method, op in {
                    method: op
                    for method, op in path_definition.items()
                    if method
                    in (
                        "get",
                        "put",
                        "post",
                        "delete",
                        "options",
                        "head",
                        "patch",
                        "trace",
                    )
                }.items():
                    op["tags"] = source.tags

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
    tag_description_map: dict[str, str] = {}
    # keep any existing definitions (base + sources without overrides)
    for existing_tag in spec.get("tags", []):
        tag_name = existing_tag.get("name")
        if tag_name:
            tag_description_map[tag_name] = existing_tag.get("description", "")
    # override or add from config.tags
    for config_tag in config.tags:
        tag_description_map[config_tag["name"]] = config_tag.get("description", "")
    # Rewrite spec["tags"] as a deduped list, preserving order of first appearance in 'tag_description_map'
    spec["tags"] = [
        {"name": name, "description": tag_description_map[name]}
        for name in tag_description_map
    ]

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
