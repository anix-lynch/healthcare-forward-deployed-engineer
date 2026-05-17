.PHONY: install serve demo test docker-up docker-down smoke acceptance clean help

help:
	@echo "Targets:"
	@echo "  install         pip install requirements"
	@echo "  serve           uvicorn on :8000"
	@echo "  demo            fire one /v1/ask via TestClient + print JSON"
	@echo "  test            pytest tests/"
	@echo "  acceptance      pytest evaluation/acceptance_tests.py"
	@echo "  docker-up       docker-compose up -d (container on :8000)"
	@echo "  docker-down     docker-compose down"
	@echo "  smoke           post-deploy smoke test against localhost:8000"

install:
	pip install -r requirements.txt

serve:
	uvicorn app.main:app --reload --port 8000

demo:
	@python -c "from fastapi.testclient import TestClient; from app.main import app; \
import json; c = TestClient(app); \
r = c.post('/v1/ask', json={'case_id': 'DEMO-001', 'chief_complaint': 'chest pain with sweating', \
'hpi': '62yo M substernal pressure with diaphoresis, jaw radiation', 'age': 62, \
'arrival_mode': 'ambulance', 'vitals': {'bp_sys': 95, 'hr': 122, 'spo2': 92}}); \
print(json.dumps(r.json(), indent=2))"

test:
	pytest tests/ -v

acceptance:
	pytest evaluation/acceptance_tests.py -v

docker-up:
	docker-compose -f deployment/docker-compose.yml up -d --build

docker-down:
	docker-compose -f deployment/docker-compose.yml down

smoke:
	bash deployment/smoke_test.sh

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache outputs/
