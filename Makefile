.PHONY: test test-cov lint typecheck setup check experiment

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov-fail-under=90 --tb=short

lint:
	pre-commit run --all-files

typecheck:
	mypy src/ scripts/ --strict

setup:
	pip install -e ".[dev]"
	pre-commit install

check: lint typecheck test-cov

experiment:
	.venv/bin/python -m src.experiment.run_experiment
