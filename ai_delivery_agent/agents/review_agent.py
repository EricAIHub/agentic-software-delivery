from __future__ import annotations

from ai_delivery_agent.llm import LLMClient
from ai_delivery_agent.models import ImplementationPlan, PatchResult, RequirementSpec


class ReviewAgent:
    name = "review_agent"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(
        self,
        requirement: str,
        spec: RequirementSpec,
        plan: ImplementationPlan,
        patch_result: PatchResult,
        test_plan: str,
    ) -> str:
        if self.llm.enabled:
            system = (
                "You are a strict code reviewer. Review the generated patch and test plan. "
                "Return concrete blocking issues, non-blocking issues, and merge recommendation."
            )
            user = f"""
Requirement:
{requirement}

Requirement spec:
{spec.model_dump_json(indent=2)}

Plan:
{plan.plan_markdown}

Patch validity:
{patch_result.model_dump_json(indent=2)}

Patch:
{patch_result.patch[:12000]}

Test plan:
{test_plan}
""".strip()
            response = self.llm.complete(system, user, max_tokens=1600)
            if response.text and not response.used_mock:
                return response.text.strip()

        validity = "valid unified diff" if patch_result.valid_unified_diff else "invalid or empty diff"
        apply_status = (
            "not applied because this was a dry run"
            if not patch_result.apply_attempted
            else ("applied successfully" if patch_result.apply_succeeded else f"apply failed: {patch_result.apply_message}")
        )
        return f"""# Review

## Summary

The generated patch is a {validity}. It was {apply_status}.

## Blocking issues

- Human review is still required. Agent output is not a substitute for ownership.
- Confirm the patch satisfies every acceptance criterion, not just the most obvious one.
- Confirm tests execute in the target repository, not merely in this orchestrator project.

## Non-blocking issues

- The current MVP does not execute tests in a sandbox.
- The current MVP does not create a remote pull request.
- The current MVP does not inspect runtime logs or production telemetry.

## Merge recommendation

Do not merge automatically. Treat this as a draft PR artifact and run the normal engineering review process.
""".strip()
