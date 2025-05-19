import json
import logging
import os.path
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional, TypedDict

import requests
import yaml

from .log import logger

HTTP_PATTERN = re.compile(r"^(http|https)://", re.IGNORECASE)
FILE_PATTERN = re.compile(r"^(file)://", re.IGNORECASE)

OpenAPISpec = dict[str, Any]


@dataclass
class Config:
    @dataclass
    class APISource:
        class Server(TypedDict):
            url: str
            description: str

        @dataclass
        class OperationsFilter:
            methods: set[str] = field(
                default_factory=lambda: {
                    "get",
                    "put",
                    "post",
                    "delete",
                    "options",
                    "head",
                    "patch",
                    "trace",
                }
            )
            tags: set[str] = field(default_factory=set)

            def __call__(self, path_definition: dict) -> Iterator[tuple[str, dict]]:
                """
                Filter paths to only include those that have the specified tags.
                """
                for op, op_definition in path_definition.items():
                    if op in self.methods:
                        if self.tags:
                            # Tags specified, check if any of them match
                            if not self.tags or (
                                set(op_definition.get("tags", [])) & self.tags
                            ):
                                yield op, op_definition
                        else:
                            # No tags specified, include all operations
                            yield op, op_definition

        url: str
        prefix: str = ""
        servers: list[Server] = field(default_factory=list)
        tags: list[str] = field(default_factory=list)
        operations_filter: OperationsFilter = field(default_factory=OperationsFilter)

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
                    tags=set(source.get("tags", [])),
                    operations_filter=Config.APISource.OperationsFilter(
                        tags=set(source.get("filters", {}).get("tags", [])),
                    ),
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


def recursive_merge(d1: dict, d2: dict, base: Optional[str] = None) -> dict:
    """Recursively merge two dictionaries. Updates d1 with values from d2."""
    for key, value in d2.items():
        # Build our dotted path for logging
        path = f"{base}.{key}" if base else key

        if isinstance(value, dict):
            # If d1[key] exists and is not a dict, replace it
            if key in d1 and not isinstance(d1[key], dict):
                logger.warning(f"Overwriting non‐dict at '{path}' with a dict")
                d1[key] = {}

            # Now safe to recurse: ensures d1[key] is a dict
            recursive_merge(d1.setdefault(key, {}), value, path)

        else:
            # Scalar or list: just overwrite
            if key in d1:
                logger.info(f"Overwriting '{path}'")
            d1[key] = value

    return d1


def get_nested_key(d: dict, key: str, *, default: Optional[Any] = None) -> Any:
    """
    Get a key from a dictionary. The key may be nested (dot separated). If the key does
    not exist, returns the default and any parent keys will be added to the dict.
    """
    result = d
    keys = key.split(".")
    for subkey in keys[:-1]:
        result = result.setdefault(subkey, {})

    return result.setdefault(keys[-1], default)


def load_spec(url: str) -> OpenAPISpec:
    """Load OpenAPI spec from a given URL or file."""
    if HTTP_PATTERN.match(url):
        return fetch_http_spec(url)
    elif FILE_PATTERN.match(url):
        return load_file_spec(url.removeprefix("file://"))
    else:
        raise ValueError(f"Unknown source type for {url}.")


def fetch_http_spec(url: str) -> OpenAPISpec:
    """Fetch OpenAPI spec from a given HTTP[S] URL."""
    _, ext = os.path.splitext(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        logger.error("Failed to fetch %s: %r", url, e)
        raise
    else:
        if ext in (".yaml", ".yml"):
            return yaml.safe_load(response.content)
        else:
            return response.json()


def load_file_spec(file_path: str) -> OpenAPISpec:
    """Load OpenAPI spec from a local file."""
    _, ext = os.path.splitext(file_path)
    try:
        with open(file_path, "rb") as file:
            if ext in (".yaml", ".yml"):
                return yaml.safe_load(file)
            else:
                return json.load(file)
    except Exception as e:
        logger.error("Failed to load %s: %r", file_path, e)
        raise


def update_tags(
    t1: list[Config.TagDefinition], t2: list[Config.TagDefinition]
) -> list[Config.TagDefinition]:
    """
    Update t1 tags from t2. If tag from t2 exists already in t1 (name matches) then
    it will be overwritten. Otherwise the tag from t2 will be appended to t1.

    A new list is returned, sorted by name. t1 and t2 are not modified.
    """
    tags = {tag["name"]: tag for tag in t1}
    for tag in t2:
        tags[tag["name"]] = tag
    return list(tags.values())
