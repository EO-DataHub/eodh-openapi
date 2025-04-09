docker ?= docker
image ?= public.ecr.aws/eodh/eodh-openapi
version ?= 0.1.0
port ?= 8000

.SILENT:
MAKEFLAGS += --no-print-directory

.PHONY: run-dev
run-dev:
	fastapi dev main.py --port=$(port)

.PHONY: container-build
container-build:
	$(docker) build -t $(image):$(version) .

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

