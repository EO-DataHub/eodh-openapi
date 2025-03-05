.PHONY: dockerbuild dockerpush test testonce ruff black lint isort pre-commit-check requirements-update requirements setup
IMAGENAME = hubapi
DOCKERREPO ?= public.ecr.aws/eodh/eodhp-hubapi
VERSION ?= 0.1.0

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
	uvicorn hubapi.__main__:app --host 0.0.0.0 --port 8000 --reload
	
test:
	./venv/bin/ptw CHANGEME-test-package-names

testonce:
	./venv/bin/pytest

ruff:
	./venv/bin/ruff check .

black:
	./venv/bin/black .

isort:
	./venv/bin/isort . --profile black

validate-pyproject:
	validate-pyproject pyproject.toml

lint: ruff black isort validate-pyproject

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
