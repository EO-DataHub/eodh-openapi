from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from hubapi.app import APISource, Config, app, fetch_openapi_docs, load_config

# Initialize FastAPI test client
client = TestClient(app)

# Sample mock OpenAPI responses
MOCK_STAC_RESPONSE = {
    "openapi": "3.1.0",
    "info": {"title": "STAC API", "version": "1.0.0"},
    "paths": {"/": {"get": {"summary": "Landing Page"}}, "/search": {"get": {"summary": "Search Items"}}},
    "components": {"schemas": {"Item": {}}},
}

MOCK_ADES_RESPONSE = {
    "openapi": "3.1.0",
    "info": {"title": "ADES API", "version": "1.0.0"},
    "paths": {"/": {"get": {"summary": "ADES Root"}}, "/processes": {"get": {"summary": "List Processes"}}},
    "components": {"schemas": {"Process": {}}},
}


@pytest.fixture
def mock_config():
    """Mocked configuration for API sources."""
    return Config(
        title="Hub API Reference",
        version="1.0.0",
        openapi_version="3.1.0",
        docs_url="/api/catalogue/docs",
        openapi_url="/api/catalogue/openapi.json",
        sources=[
            APISource(name="STAC FastAPI", prefix="/api/catalogue/stac", url="https://mock-stac/api"),
            APISource(name="ADES", prefix="/ades", url="https://mock-ades/api"),
        ],
    )


@pytest.fixture
def mock_requests_get(mocker):
    """Mock `requests.get` to return predefined OpenAPI responses."""

    def mock_get(url, *args, **kwargs):
        response_mock = MagicMock()
        if "mock-stac" in url:
            response_mock.json.return_value = MOCK_STAC_RESPONSE
        elif "mock-ades" in url:
            response_mock.json.return_value = MOCK_ADES_RESPONSE
        response_mock.raise_for_status = MagicMock()
        return response_mock

    return mocker.patch("requests.get", side_effect=mock_get)


def test_fetch_openapi_docs(mock_config, mock_requests_get):
    """Test OpenAPI merging logic with mocked API responses."""
    with patch("hubapi.app.config", mock_config):
        merged_openapi = fetch_openapi_docs()

    assert merged_openapi["info"]["title"] == "Hub API Reference"
    assert merged_openapi["info"]["version"] == "1.0.0"
    assert "/api/catalogue/stac/" in merged_openapi["paths"]
    assert "/ades/" in merged_openapi["paths"]
    assert "tags" in merged_openapi
    assert any(tag["name"] == "STAC FastAPI" for tag in merged_openapi["tags"])
    assert any(tag["name"] == "ADES" for tag in merged_openapi["tags"])


def test_openapi_endpoint(mock_requests_get):
    """Test that /api/catalogue/openapi.json returns a valid response."""
    response = client.get("/api/catalogue/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


def test_docs_redirect():
    """Test that root URL redirects to /api/catalogue/docs."""
    response = client.get("/")

    assert response.status_code in [200, 307]

    if response.status_code == 307:
        assert response.headers["location"] == "/api/catalogue/docs"


def test_load_config(mocker):
    """Test loading of configuration from YAML."""
    mock_yaml_content = """
    title: "Test API"
    version: "2.0.0"
    openapi_version: "3.1.0"
    docs_url: "/test/docs"
    openapi_url: "/test/openapi.json"
    sources:
      - name: "STAC"
        prefix: "/api/catalogue/stac"
        url: "https://mock-stac/api"
    """

    with (
        patch("builtins.open", mocker.mock_open(read_data=mock_yaml_content)),
        patch("os.getenv", return_value="/mock/config.yaml"),
        patch("os.path.exists", return_value=True),
    ):
        config = load_config("/mock/config.yaml")

    assert config.title == "Test API"
    assert config.version == "2.0.0"
    assert config.docs_url == "/test/docs"
    assert config.openapi_url == "/test/openapi.json"
    assert len(config.sources) == 1
    assert config.sources[0].name == "STAC"
