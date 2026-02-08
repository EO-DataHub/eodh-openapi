from eodh_openapi.utils import recursive_merge


def test_merge_spec__no_conflicts__success() -> None:
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "tags": ["test 1"],
        "paths": {
            "/test1": {
                "get": {
                    "summary": "Test Endpoint",
                    "responses": {"200": {"description": "Success"}},
                },
            },
        },
        "components": {
            "schemas": {
                "TestSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
    }
    other = {
        "openapi": "3.1.0",
        "info": {
            "title": "Other API",
            "version": "1.0.0",
            "description": "Other API Description",
        },
        "paths": {
            "/other1": {
                "get": {
                    "summary": "Test Endpoint",
                    "responses": {"200": {"description": "Success"}},
                },
            },
            "/other2": {
                "get": {
                    "summary": "Other Endpoint",
                    "responses": {"200": {"description": "Success"}},
                },
            },
        },
        "components": {
            "schemas": {
                "OtherSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
    }

    # pre checks
    assert len(spec["paths"]) == 1
    assert len(spec["components"]["schemas"]) == 1

    # unit under test
    for key in ("paths", "components"):
        recursive_merge(spec[key], other[key])

    # post checks
    assert len(spec["paths"]) == 3
    assert len(spec["components"]["schemas"]) == 2
