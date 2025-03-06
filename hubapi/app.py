import os
from dataclasses import dataclass, field

import requests
import yaml
from fastapi import FastAPI
from fastapi.responses import RedirectResponse


@dataclass
class APISource:
    name: str
    prefix: str
    url: str


@dataclass
class Config:
    sources: list[APISource] = field(default_factory=list)


def load_config(filename: str | None) -> Config:
    """Loads configuration from a YAML file."""
    if filename and os.path.exists(filename):
        with open(filename, "r") as f:
            config_data = yaml.safe_load(f)
            sources = [
                APISource(name=entry["name"], prefix=entry["prefix"], url=entry["url"])
                for entry in config_data.get("sources", [])
            ]
            return Config(sources=sources)
    return Config()


# Load config from the environment variable
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config/config.yaml")
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
        "tags": [],
        "paths": {},
        "components": {"schemas": {}},
    }

    for source in config.sources:
        try:
            response = requests.get(source.url)
            response.raise_for_status()
            api_spec = response.json()

            # Add a tag for this API in Swagger UI (only if not already added)
            if not any(tag["name"] == source.name for tag in merged_api["tags"]):
                merged_api["tags"].append(
                    {"name": source.name, "description": f"Endpoints from {source.name}"}
                )

            # Merge paths using the defined prefix
            if "paths" in api_spec:
                for path, methods in api_spec["paths"].items():
                    new_path = f"{source.prefix}{path}" if not path.startswith(source.prefix) else path
                    if new_path not in merged_api["paths"]:
                        merged_api["paths"][new_path] = {}

                    for method, details in methods.items():
                        details.setdefault("tags", []).append(source.name)  # Assign tag to this endpoint
                        merged_api["paths"][new_path][method] = details

            # Merge schemas
            if "components" in api_spec and "schemas" in api_spec["components"]:
                merged_api["components"]["schemas"].update(api_spec["components"]["schemas"])

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Failed to fetch {source.url}: {e}")

    return merged_api


@app.get("/")
async def redirect_to_docs():
    """Redirects to /api/catalogue/docs."""
    return RedirectResponse(url="/api/catalogue/docs")


# Override FastAPI’s OpenAPI function
app.openapi = fetch_openapi_docs
