.PHONY: all setup test run_a run_b

all: run_a run_b

setup:
	pip install -r requirements.txt

test:
	pytest

run_a:
	python -m project_a.run_all

run_b:
	python -m project_b.run_all

