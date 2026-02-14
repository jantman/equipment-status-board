.PHONY: setup db-up migrate run worker test test-e2e lint docker-build docker-up

VENV := venv
FLASK_APP := esb:create_app

setup:
	python -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements-dev.txt

db-up:
	docker compose up -d db

migrate:
	FLASK_APP=$(FLASK_APP) $(VENV)/bin/flask db upgrade

run:
	FLASK_APP=$(FLASK_APP) $(VENV)/bin/flask run --debug

worker:
	FLASK_APP=$(FLASK_APP) $(VENV)/bin/flask worker run

test:
	$(VENV)/bin/python -m pytest tests/ -v

test-e2e:
	$(VENV)/bin/python -m pytest tests/e2e/ -v

lint:
	$(VENV)/bin/ruff check esb/ tests/

docker-build:
	docker compose build

docker-up:
	docker compose up
