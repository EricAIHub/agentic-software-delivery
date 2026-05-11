from __future__ import annotations

from fastapi import FastAPI, HTTPException

from ai_delivery_agent.models import DeliveryResult, RunRequest
from ai_delivery_agent.orchestrator import DeliveryOrchestrator

app = FastAPI(title="AI Delivery Agent MVP", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run", response_model=DeliveryResult)
def run_delivery(request: RunRequest) -> DeliveryResult:
    try:
        orchestrator = DeliveryOrchestrator()
        return orchestrator.run(
            repo_path=request.repo_path,
            requirement=request.requirement,
            max_files=request.max_files,
            dry_run=request.dry_run,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - API guardrail
        raise HTTPException(status_code=500, detail=f"Agent run failed: {exc}") from exc
