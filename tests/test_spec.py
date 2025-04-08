from eodh_openapi import OpenAPISpec


def test_merge_spec__no_conflicts__success():
    spec = OpenAPISpec(
        openapi="3.1.0",
        info=OpenAPISpec.Info(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        ),
        paths={
            "/test1": {
                "get": {
                    "summary": "Test Endpoint",
                    "responses": {"200": {"description": "Success"}},
                },
            },
        },
        components={
            "schemas": {
                "TestSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
        tags=["Test Tag"],
    )
    other = OpenAPISpec(
        openapi="3.1.0",
        info=OpenAPISpec.Info(
            title="Other API",
            version="1.0.0",
            description="Other API Description",
        ),
        paths={
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
        components={
            "schemas": {
                "OtherSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
    )
    assert len(spec.paths) == 1
    assert len(spec.components) == 1
    spec.merge(other)
    assert len(spec.paths) == 3
    assert len(spec.components) == 2
