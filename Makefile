SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND  := backend
COMPOSE  := docker compose
API_PORT := 8000

.PHONY: help up down stop db db-stop api api-stop migrate health status logs-db psql notebook wipe

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

## ---------------------------------------------------------------- compound

up: db migrate api  ## Start db (if down), apply migrations, then run API (blocks)

down: api-stop db-stop  ## Stop API and database

stop: down  ## Alias for `down`

## ---------------------------------------------------------------- database

db:  ## Start Postgres container (idempotent); waits for it to be healthy
	@$(COMPOSE) up -d db
	@echo "Waiting for Postgres to be ready..."
	@until $(COMPOSE) exec -T db pg_isready -U mathpath >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres ready."

db-stop:  ## Stop Postgres container (data preserved on volume)
	@$(COMPOSE) stop db

## ---------------------------------------------------------------- api

api:  ## Start uvicorn in the foreground (assumes db is up)
	@cd $(BACKEND) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(API_PORT)

api-stop:  ## Kill whatever is listening on $(API_PORT)
	@pids=$$(lsof -ti tcp:$(API_PORT) 2>/dev/null | tr '\n' ' '); \
	if [ -n "$$pids" ]; then echo "killing pid(s): $$pids"; kill $$pids; else echo "nothing on port $(API_PORT)"; fi

migrate:  ## Apply any pending Alembic migrations
	@cd $(BACKEND) && uv run alembic upgrade head

## ---------------------------------------------------------------- diagnostics

health:  ## Hit /api/health and print the HTTP status
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:$(API_PORT)/api/health \
		|| echo "API not reachable on port $(API_PORT)"

status:  ## Show what's running (db + api)
	@echo "== docker services =="
	@$(COMPOSE) ps
	@echo
	@echo "== port $(API_PORT) =="
	@pids=$$(lsof -ti tcp:$(API_PORT) 2>/dev/null | tr '\n' ' '); \
	if [ -n "$$pids" ]; then echo "API running (pid(s): $$pids)"; else echo "API not running"; fi

logs-db:  ## Tail Postgres logs
	@$(COMPOSE) logs -f db

psql:  ## Open a psql shell inside the db container
	@$(COMPOSE) exec db psql -U mathpath -d mathpath

## ---------------------------------------------------------------- dev tools

notebook:  ## Launch Jupyter Lab on tests/notebooks (no token, localhost only)
	@cd $(BACKEND) && uv run --group dev jupyter lab tests/notebooks/ \
		--ServerApp.token='' --ServerApp.password=''

wipe:  ## Wipe a book: `make wipe BOOK_ID=<uuid>` (or `BOOK_ID=--all`)
	@if [ -z "$(BOOK_ID)" ]; then echo "Usage: make wipe BOOK_ID=<uuid>|--all"; exit 1; fi
	@cd $(BACKEND) && uv run python scripts/wipe_book.py $(BOOK_ID) --yes
