.PHONY: test lint demo figures web

test:
	pytest -q

lint:
	ruff check src tests scripts

demo:
	python scripts/run_analysis.py --demo

figures:
	python scripts/make_figures.py --demo

web:
	cd web-react && npm run build
