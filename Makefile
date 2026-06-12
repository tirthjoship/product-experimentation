.PHONY: test test-cov lint typecheck setup check experiment scenarios motivation did-feasibility did-gate did dashboard dashboard-smoke

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov=dashboard --cov-fail-under=90 --tb=short

lint:
	pre-commit run --all-files

typecheck:
	mypy src/ scripts/ dashboard/ --strict

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

dashboard:
	.venv/bin/python -m streamlit run dashboard/app.py

dashboard-smoke:
	.venv/bin/python scripts/dashboard_smoke.py
