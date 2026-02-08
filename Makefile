VERSION ?= latest
IMAGENAME = eodh-openapi
DOCKERREPO ?= public.ecr.aws/eodh
uv-run ?= uv run --no-sync
port ?= 8000
output ?= eodh_openapi/web/static/openapi.json
static ?= eodh_openapi/web/static

.PHONY: dockerbuild
dockerbuild:
	DOCKER_BUILDKIT=1 docker build -t ${IMAGENAME}:${VERSION} .

.PHONY: dockerpush
dockerpush: dockerbuild
	docker tag ${IMAGENAME}:${VERSION} ${DOCKERREPO}/${IMAGENAME}:${VERSION}
	docker push ${DOCKERREPO}/${IMAGENAME}:${VERSION}

.PHONY: run-dev
run-dev:
	${uv-run} python -m eodh_openapi spec serve --port=$(port) --static-dir=$(static)

.PHONY: generate
generate:
	${uv-run} python -m eodh_openapi spec generate --config=$(config) \
	  --output=$(output)

.PHONY: container-run
container-run: dockerbuild
	docker run --rm \
	--mount type=bind,source=$(PWD)/$(static),target=/app/$(static) \
	-p $(port):8000 ${IMAGENAME}:${VERSION}

.PHONY: test
test:
	${uv-run} ptw .

.PHONY: testonce
testonce:
	${uv-run} pytest

.git/hooks/pre-commit:
	${uv-run} pre-commit install
	curl -o .pre-commit-config.yaml https://raw.githubusercontent.com/EO-DataHub/github-actions/main/.pre-commit-config-python.yaml

.PHONY: setup
setup: update .git/hooks/pre-commit

.PHONY: pre-commit
pre-commit:
	${uv-run} pre-commit

.PHONY: pre-commit-all
pre-commit-all:
	${uv-run} pre-commit run --all-files

.PHONY: check
check:
	${uv-run} ruff check
	${uv-run} ruff format --check --diff
	${uv-run} pyright
	${uv-run} validate-pyproject pyproject.toml

.PHONY: format
format:
	${uv-run} ruff check --fix
	${uv-run} ruff format

.PHONY: install
install:
	uv sync --frozen

.PHONY: update
update:
	uv sync
