import os.path
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient

from eodh_openapi.web import create_app


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copy(
            src=os.path.join(os.path.dirname(__file__), "files/spec.json"),
            dst=os.path.join(temp_dir, "test.json"),
        )
        with open(os.path.join(temp_dir, "test.json")) as spec_file:
            app = create_app(
                title="Test API", openapi_spec=spec_file.name, static_dir=temp_dir
            )
            yield TestClient(app, base_url="https://test.org.uk")


def test_get_docs__html__success(client):
    """Test the home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_get_spec__json__success(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_get_spec__spec_missing__file_not_found():
    with tempfile.TemporaryDirectory() as temp_dir:
        app = create_app(
            title="Test API", openapi_spec="missing.json", static_dir=temp_dir
        )
        client = TestClient(app, base_url="https://test.org.uk")
        response = client.get("/openapi.json")

    assert response.status_code == 404
