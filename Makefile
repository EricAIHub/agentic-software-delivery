install:
	python -m pip install -e ".[dev]"

run-api:
	uvicorn ai_delivery_agent.main:app --reload --host 0.0.0.0 --port 8000

run-sample:
	python -m ai_delivery_agent.cli --repo ./sample_repo --requirement "Add a /health endpoint that returns {'status':'ok'} and add a simple test plan." --output ./.agent_runs/sample

test:
	pytest -q
