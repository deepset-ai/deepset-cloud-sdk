# Development and Testing
.PHONY: tests-with-cov tests-unit tests-integration unit-with-cov integration
tests-with-cov:
	uv run pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=deepset_cloud_sdk tests/unit

tests-unit:
	uv run pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=deepset_cloud_sdk tests/unit

tests-integration:
	uv run pytest tests/integration

unit-with-cov:
	uv run pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=deepset_cloud_sdk tests/unit

integration:
	uv run pytest --cov-report=term-missing --cov-config=pyproject.toml --cov=deepset_cloud_sdk tests/integration

# Code Quality
.PHONY: types format format-fix lint lint-fix hooks all all-fix
types:
	uv run mypy deepset_cloud_sdk tests

format:
	uv run ruff format deepset_cloud_sdk tests --check

format-fix:
	uv run ruff format deepset_cloud_sdk tests

lint:
	uv run ruff check deepset_cloud_sdk tests

lint-fix:
	uv run ruff check --fix deepset_cloud_sdk tests

hooks:
	uv run pre-commit install

all: types format lint

all-fix: format-fix lint-fix

# Build and Deploy
.PHONY: build
build:
	uv build

