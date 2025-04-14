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
            src=os.path.join(os.path.dirname(__file__), "files/spec.yaml"),
            dst=os.path.join(temp_dir, "test.yaml"),
        )
        with open(os.path.join(temp_dir, "test.yaml")) as spec_file:
            app = create_app(
                title="Test API", openapi_spec=spec_file.name, static_dir=temp_dir
            )
            yield TestClient(app, base_url="https://test.org.uk")


def test_get_docs__html__success(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_get_spec__json__success(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
