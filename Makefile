.PHONY: test test-cov lint typecheck setup check experiment scenarios motivation did-feasibility did-gate did

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

scenarios:
	python -m src.experiment.run_experiment --scenarios

motivation:
	python -m src.report.installment_motivation

did-feasibility:
	python -m src.did.run_did --stage feasibility

did-gate:
	python -m src.did.run_did --stage gate

did:
	python -m src.did.run_did --stage estimate
