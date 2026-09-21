.PHONY: test lint demo

test:
	python -m pytest

lint:
	ruff check src tests
	ruff format --check src tests

demo:
	catalogwatch fetch --store https://www.allbirds.com --out out/demo.csv --max-pages 1
	head -3 out/demo.csv
