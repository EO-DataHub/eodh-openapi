docker ?= docker
image ?= public.ecr.aws/eodh/eodh-openapi
version ?= 0.1.1
port ?= 8000
output ?= eodh_openapi/web/static/openapi.json
static ?= eodh_openapi/web/static

.SILENT:
MAKEFLAGS += --no-print-directory

.PHONY: run-dev
run-dev:
	python -m eodh_openapi spec serve --port=$(port) --static-dir=$(static)

.PHONY: generate
generate:
	python -m eodh_openapi spec generate --config=$(config) \
	  --output=$(output)

.PHONY: container-build
container-build:
	$(docker) build -t $(image):$(version) .

.PHONY: container-run
container-run:
	$(docker) run --rm \
	--mount type=bind,source=$(PWD)/$(static),target=/app/$(static) \
	-p $(port):8000 $(image):$(version)

.PHONY: container-push
container-push:
	$(docker) push $(image):$(version)

.PHONY: publish
publish: container-build container-push

.PHONY: check
check:
	ruff check . --select I --fix

.PHONY: fmt
fmt:
	ruff format .

.PHONY: test
test:
	python -m pytest -v .

