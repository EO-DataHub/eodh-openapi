import json
import os.path
from typing import Any

import click
import uvicorn
import yaml

from . import utils, web
from .log import logger


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
@click.option(
    "--fail-on-missing-source/--no-fail-on-missing-source",
    default=False,
    help="If set, abort on any source load failure (instead of skipping).",
)
def generate(config_file: str, output_file: str, fail_on_missing_source: bool):
    """
    Generate OpenAPI spec from multiple sources into a single spec.
    """
    config = utils.Config.load(config_file)
    logger.info(f"Loaded config from {config_file}")

    # Load base OpenAPI spec
    try:
        spec = utils.load_spec(config.base_url)
    except Exception as e:
        logger.error(f"Failed to load base OpenAPI spec: {e}")
        raise
    else:
        logger.info(f"Loaded base OpenAPI spec from {config.base_url}")

    # Initialise tags in the spec if not present
    spec.setdefault("tags", [])

    # Merge all sources into the OpenAPI spec
    for source in config.sources:
        try:
            other = utils.load_spec(source.url)
        except Exception as e:
            logger.error(f"Failed to load spec from {source.url}: {e}.")
            if fail_on_missing_source:
                raise click.ClickException(
                    f"Failed to load spec from {source.url}: {e}."
                )
            logger.info("Skipping this source and continuing with the next one.")
            continue
        else:
            logger.info(f"Merging spec from {source.url} into base spec.")

        # If we are not overwriting tags for this source then add original spec tag definitions
        if not source.tags:
            spec["tags"].extend(other.get("tags", []))

        # Iterate over the paths and update the fields where required
        new_paths: dict[str, Any] = {}
        for path, path_definition in other.setdefault("paths", {}).items():
            # Extract the operations from the path definition and retag if necessary
            operations = dict(source.operations_filter(path_definition))
            if not operations:
                # no matching ops found
                continue

            # retag those operations if the source specified tags
            if source.tags:
                for op_def in operations.values():
                    op_def["tags"] = list(source.tags)

            # carry over any servers you want at the path‐level
            operations.setdefault("servers", []).extend(source.servers)

            new_paths[f"{source.prefix}{path}"] = operations

        # Add modified other paths to the base spec
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

    # Update or append spec tags from source config
    spec["tags"] = sorted(
        utils.update_tags(spec["tags"], config.tags), key=lambda x: x["name"]
    )  # Sort the tags by name

    # Output the final spec
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
