.RECIPEPREFIX = >
.PHONY: setup test spot-check stress-test build-suite build-site lint fmt security clean docs

setup:
> pip install -e ".[all,dev,suite,verify,docs]"
> pre-commit install || true

test:
> pytest -v

spot-check:
> python spot_check.py

stress-test:
> python stress_test.py

build-suite:
> python build.py

build-site:
> python web/build_site.py

lint:
> ruff check src tests

fmt:
> ruff check --fix src tests

security:
> gitleaks detect --source . --redact -v

docs:
> mkdocs serve

clean:
> rm -rf _site build dist *.egg-info .pytest_cache .ruff_cache
> find . -type d -name __pycache__ -exec rm -rf {} +
