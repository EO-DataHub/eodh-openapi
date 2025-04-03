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

.PHONY: validate-pyproject
validate-pyproject:
	validate-pyproject pyproject.toml

.PHONY: lint
lint: ruff fmt validate-pyproject

.PHONY: requirements.txt
requirements.txt:
	pip-compile -q --strip-extras

.PHONY: requirements-dev.txt
requirements-dev.txt:
	pip-compile -q --strip-extras --extra dev -o requirements-dev.txt

.PHONY: requirements
requirements: requirements.txt requirements-dev.txt

.PHONY: requirements-update
requirements-update: venv
	./venv/bin/pip-compile -U
	./venv/bin/pip-compile --extra dev -o requirements-dev.txt -U


.PHONY: venv
venv:
	virtualenv -p python3.11 venv
	./venv/bin/pip3 install pip-tools

.make-venv-installed: venv requirements.txt requirements-dev.txt
	./venv/bin/pip3 install -r requirements.txt -r requirements-dev.txt
	touch .make-venv-installed

.git/hooks/pre-commit:
	./venv/bin/pre-commit install
	curl -o .pre-commit-config.yaml https://raw.githubusercontent.com/EO-DataHub/github-actions/main/.pre-commit-config-python.yaml

.PHONY: setup
setup: venv requirements .make-venv-installed .git/hooks/pre-commit
