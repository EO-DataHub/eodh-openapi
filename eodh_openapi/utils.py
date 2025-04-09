import json
import os.path
import re
from typing import Any, Optional

import requests
import yaml

from .log import logger

HTTP_PATTERN = re.compile(r"^(http|https)://", re.IGNORECASE)
FILE_PATTERN = re.compile(r"^(file)://", re.IGNORECASE)

OpenAPISpec = dict[str, Any]


def recursive_merge(d1: dict, d2: dict, base: Optional[str] = None) -> dict:
    """Recursively merge two dictionaries. Updates d1 with values from d2."""
    for key, value in d2.items():
        if isinstance(value, dict):
            recursive_merge(d1.setdefault(key, {}), value, f"{base}.{key}")
        else:
            if key in d1:
                logger.warning(f"Overwriting key '{base}.{key}' in dictionary.")
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
        print(f"Failed to fetch {url}: {e}")
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
        print(f"Failed to load {file_path}: {e}")
        raise
