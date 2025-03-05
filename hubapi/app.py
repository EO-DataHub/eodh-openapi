import os
from dataclasses import dataclass, field

import requests
import yaml
from fastapi import FastAPI
from fastapi.responses import RedirectResponse


@dataclass
class Config:
    sources: list[str] = field(default_factory=list)


def load_config(filename: str | None) -> Config:
    """Loads configuration from a YAML file."""
    if filename and os.path.exists(filename):
        with open(filename, "r") as f:
            config_data = yaml.safe_load(f)
            return Config(sources=config_data.get("sources", []))
    return Config()


# Load config from the mounted ConfigMap file
CONFIG_FILE = os.environ.get("CONFIG_FILE", "/config/config.yaml")
config = load_config(CONFIG_FILE)

app = FastAPI(
    title="Hub API Reference",
    version="1.0.0",
    docs_url="/api/catalogue/docs",
    openapi_url="/api/catalogue/openapi.json",
)


def fetch_openapi_docs():
    """Fetch and merge OpenAPI JSON dynamically from multiple sources."""
    merged_api = {
        "openapi": "3.1.0",
        "info": {"title": "Hub API Reference", "version": "1.0.0"},
        "paths": {},
        "components": {"schemas": {}},
    }

    for url in config.sources:
        url = url.strip()
        if not url:
            continue

        try:
            response = requests.get(url)
            response.raise_for_status()
            api_spec = response.json()

            # Merge paths
            if "paths" in api_spec:
                for path, methods in api_spec["paths"].items():
                    new_path = f"/api/catalogue{path}"
                    merged_api["paths"].setdefault(new_path, {}).update(methods)

            # Merge schemas
            if "components" in api_spec and "schemas" in api_spec["components"]:
                merged_api["components"]["schemas"].update(api_spec["components"]["schemas"])

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    return merged_api


@app.get("/")
async def redirect_to_docs():
    """Redirects to /api/catalogue/docs."""
    return RedirectResponse(url="/api/catalogue/docs")


# Override FastAPI’s OpenAPI function
app.openapi = fetch_openapi_docs
