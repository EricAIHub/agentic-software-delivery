# Agentic Software Delivery

A multi-agent engineering workflow that converts product requirements into repository-aware implementation plans, code patches, test plans, and review reports.

The project is intentionally small enough to run locally, but the architecture mirrors a production multi-agent workflow:

1. **Requirement Agent**: decomposes the requirement into pain point, user stories, acceptance criteria, constraints, and risks.
2. **Repo Scanner Agent**: scans the codebase, builds a file tree, summarizes language composition, and extracts bounded file snippets.
3. **Planner Agent**: identifies likely files to change and writes an implementation plan.
4. **Code Agent**: generates a unified diff patch. With no API key, it runs in deterministic mock mode and produces a planning artifact patch. With an API key, it asks the model to generate code-level changes.
5. **Test Agent**: proposes verification steps and regression coverage.
6. **Review Agent**: checks the generated diff for maintainability, risk, and missing validation.

## Quick start

```bash
cd ai_delivery_agent_mvp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Optional: edit `.env` and set `OPENAI_API_KEY`. Without a key, the system still runs, but it will not generate real repository-specific code changes.

## Run from CLI

```bash
python -m ai_delivery_agent.cli \
  --repo ./sample_repo \
  --requirement "Add a /health endpoint that returns {'status':'ok'} and explain how to test it." \
  --output ./.agent_runs/sample
```

Artifacts will be written to the output directory:

- `01_requirement.json`
- `02_repo_summary.json`
- `03_plan.md`
- `04_patch.diff`
- `05_test_plan.md`
- `06_review.md`
- `result.json`

## Run as API

```bash
uvicorn ai_delivery_agent.main:app --reload --host 0.0.0.0 --port 8000
```

Then call:

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "./sample_repo",
    "requirement": "Add a /health endpoint that returns status ok.",
    "max_files": 20,
    "dry_run": true
  }'
```

## Apply generated patch

By default the system only generates a patch. To apply it from the CLI:

```bash
python -m ai_delivery_agent.cli \
  --repo ./sample_repo \
  --requirement "Add a /health endpoint that returns {'status':'ok'}" \
  --output ./.agent_runs/apply-demo \
  --apply
```

The system uses `git apply`. Keep `dry_run=true` or omit `--apply` until the patch has been reviewed.

## Notes

This is an MVP. It deliberately avoids hard production problems such as sandboxed execution, authenticated GitHub/GitLab PR creation, long-running queues, enterprise permissions, and CI integration. Those belong in a production version, not in a small local demo.
