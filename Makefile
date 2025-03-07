.PHONY: dockerbuild dockerpush test testonce ruff lint pre-commit-check requirements-update requirements setup
docker ?= docker
image ?= public.ecr.aws/eodh/eodhp-docs
version ?= 0.1.0

.SILENT:
MAKEFLAGS += --no-print-directory

.PHONY: container-build
container-build:
	$(docker) build -t $(image):$(version) .

.PHONY: container-push
container-push:
	$(docker) push $(image):$(version)

.PHONY: run-dev
run-dev:
	fastapi run hubapi/app.py

.PHONY: run
run:
	fastapi run hubapi/app.py

.PHONY: ruff
ruff:
	./venv/bin/ruff check .

.PHONY: fmt
fmt:
	./venv/bin/ruff check . --select I --fix
	./venv/bin/ruff format .

test:
	./venv/bin/ptw eodhp_docs

testonce:
	./venv/bin/pytest

validate-pyproject:
	validate-pyproject pyproject.toml

lint: ruff validate-pyproject

requirements.txt: venv pyproject.toml
	./venv/bin/pip-compile

requirements-dev.txt: venv pyproject.toml
	./venv/bin/pip-compile --extra dev -o requirements-dev.txt

requirements: requirements.txt requirements-dev.txt

requirements-update: venv
	./venv/bin/pip-compile -U
	./venv/bin/pip-compile --extra dev -o requirements-dev.txt -U

venv:
	virtualenv -p python3.11 venv
	./venv/bin/pip3 install pip-tools

.make-venv-installed: venv requirements.txt requirements-dev.txt
	./venv/bin/pip3 install -r requirements.txt -r requirements-dev.txt
	touch .make-venv-installed

.git/hooks/pre-commit:
	./venv/bin/pre-commit install
	curl -o .pre-commit-config.yaml https://raw.githubusercontent.com/EO-DataHub/github-actions/main/.pre-commit-config-python.yaml

setup: venv requirements .make-venv-installed .git/hooks/pre-commit
