# UK EO DataHub OpenAPI Docs

This app merges OpenAPI v3 spec docs from multiple sources and serves them as a single document.

## Usage

### Generating the Combined OpenAPI Spec File

To generate the combined OpenAPI spec file, you must first create a base OpenAPI v3 configuration. This will be the metadata for your spec.

```yaml base.yaml
openapi: 3.1.0
info:
  title: UK EO DataHub API
  description: API documentation for the UK EO DataHub platform
  version: 0.1.0
servers:
  - url: https://eodatahub.org.uk
    description: "UK EO DataHub Platform Domain"
```

Now create two local specs to be merged into your spec.

```json users.json
{
  "paths": {
    "/users": {
      "get": {
        "tags": ["Users"],
        "responses": {
          "200": { "description": "OK" },
          "404": { "description": "Not Found" }
        }
      },
      "post": {
        "tags": ["Users"],
        "responses": {
          "201": { "description": "Created" },
          "400": { "description": "Bad Request" }
        }
      }
    },
    "/users/{user}": {
      "get": {
        "tags": ["Users"],
        "responses": {
          "200": { "description": "OK" },
          "404": { "description": "Not Found" }
        }
      }
    }
  }
}
```

```json workspaces.json
{
  "paths": {
    "/workspaces": {
      "get": {
        "tags": ["Workspaces"],
        "responses": {
          "200": { "description": "OK" },
          "404": { "description": "Not Found" }
        }
      },
      "post": {
        "tags": ["Workspaces"],
        "responses": {
          "201": { "description": "Created" },
          "400": { "description": "Bad Request" }
        }
      }
    },
    "/workspaces/{workspace}": {
      "get": {
        "tags": ["Workspaces"],
        "responses": {
          "200": { "description": "OK" },
          "404": { "description": "Not Found" }
        }
      }
    }
  }
}
```

Finally, create the config that defines the sources of the specs to be merged. URL prefixes `file://` and `http[s]://` can be used to load specs from local file or the internet, respectively.

```yaml
base_url: file://base.yaml
merge_keys:
  - paths
  - components
sources:
  - url: file://users.json
    prefix: /api
    servers:
      - url: https://eodatahub.org.uk
        description: UK EO DataHub Platform Domain
  - url: file://workspaces.json
    prefix: /api
    servers:
      - url: https://eodatahub.org.uk
        description: UK EO DataHub Platform Domain
  # - url: https://eodatahub.org.uk/api/docs/workflow-runner/openapi.json
  #   servers:
  #     - url: https://eodatahub.org.uk
  #       description: UK EO DataHub Platform Domain
```

With the configuration complete, you can now generate the combined OpenAPI spec. This will generate the combined openapi.json spec and, by default, output it to a local static directory in the eodh_openapi/web/static directory ready to be served by the app.

```bash
make generate config=config.yaml
```

### Serving the OpenAPI Spec

To serve the generated OpenAPI spec over HTTP, ensure you have a static directory with the spec inside it. By default this is eodh_openapi/web/static, but you can change it via command line options if required.

```bash
make run-dev
```

### Help

Common commands have been included in the Makefile. To discover all options available, use the help command directly on the eodh_openapi app.

```bash
uv run python -m eodh_openapi spec generate --help
uv run python -m eodh_openapi spec serve --help
```

## Development

### Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. To set up the development environment:

```bash
make setup
```

This will install all dependencies and set up pre-commit hooks.

### Running Tests

```bash
make testonce    # run tests once
make test        # run tests in watch mode
```

### Code Quality

```bash
make format      # auto-format code
make check       # run all linters and type checking
```

### Docker

Build and run the container locally:

```bash
make dockerbuild
make container-run
```

Push to ECR:

```bash
make dockerpush
```

### Release

All official releases should be performed through GitHub by creating a release and tagging it with a tag matching the form v1.2.3. Release versions should follow semver.
