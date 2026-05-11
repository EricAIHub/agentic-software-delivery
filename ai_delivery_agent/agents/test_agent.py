from __future__ import annotations

from ai_delivery_agent.llm import LLMClient
from ai_delivery_agent.models import ImplementationPlan, RequirementSpec


class TestAgent:
    name = "test_agent"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, requirement: str, spec: RequirementSpec, plan: ImplementationPlan, patch: str) -> str:
        if self.llm.enabled:
            system = (
                "You are a pragmatic QA engineer. Produce a concise test plan for the patch. "
                "Include unit, integration, regression, and manual checks where relevant."
            )
            user = f"""
Requirement:
{requirement}

Acceptance criteria:
{chr(10).join(f'- {item}' for item in spec.acceptance_criteria)}

Implementation plan:
{plan.plan_markdown}

Generated patch:
{patch[:12000]}

Write the test plan.
""".strip()
            response = self.llm.complete(system, user, max_tokens=1400)
            if response.text and not response.used_mock:
                return response.text.strip()

        return f"""# Test Plan

## Acceptance checks
{chr(10).join(f'- Verify: {item}' for item in spec.acceptance_criteria) or '- Verify the stated requirement end to end.'}

## Unit tests
- Add focused tests around the changed function, route, or service.
- Cover the expected success path.
- Cover invalid or missing inputs if the requirement touches input handling.

## Integration tests
- Start the application in the normal local mode.
- Exercise the changed API or user flow.
- Confirm response shape, status code, and side effects.

## Regression checks
- Run the existing test suite.
- Inspect nearby code paths touched by selected files: {', '.join(plan.selected_files) or 'none'}.

## Review gate
- Do not merge until the generated diff is manually reviewed and tests are green.
""".strip()
