.PHONY: install test smoke cov format lint typecheck demo seed run

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

smoke:
	python -m pytest -m smoke -v

cov:
	python -m pytest tests/ --cov=src --cov-report=term-missing

format:
	black src tests scripts main.py
	isort src tests scripts main.py

lint:
	black --check src tests scripts main.py
	isort --check-only src tests scripts main.py

typecheck:
	mypy src

demo:
	python -m scripts.demo

seed:
	python -m scripts.seed_accounts

run:
	python -m main
