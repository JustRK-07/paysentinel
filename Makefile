PY ?= python3
PIP ?= python3 -m pip

.PHONY: help install install-dev test lint run-api run-web demo clean

help:
	@echo "PaySentinel — common targets:"
	@echo "  make install       Install runtime deps"
	@echo "  make install-dev   Install runtime + dev deps"
	@echo "  make test          Run pytest"
	@echo "  make lint          Run ruff"
	@echo "  make run-api       Start FastAPI scoring service on :8000"
	@echo "  make run-web       Start Next.js prototype on :3000"
	@echo "  make demo          Run end-to-end demo (Identify -> Generate -> Defend -> Loop)"
	@echo "  make clean         Remove caches"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio ruff

test:
	$(PY) -m pytest tests/

lint:
	$(PY) -m ruff check .

run-api:
	$(PY) -m uvicorn defend.api:app --reload --host 0.0.0.0 --port 8000

run-web:
	cd webapp && npm install && npm run dev

demo:
	$(PY) -m identify.threat_landscape
	$(PY) -m generate.pipeline --config configs/demo.yaml
	$(PY) -m defend.train --config configs/demo.yaml
	$(PY) -m closed_loop.pipeline --config configs/demo.yaml --iterations 3

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ */__pycache__ */*/__pycache__
	find . -name "*.pyc" -delete
