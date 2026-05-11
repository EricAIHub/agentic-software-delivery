from __future__ import annotations

import re
from typing import List

from ai_delivery_agent.llm import LLMClient
from ai_delivery_agent.models import RequirementSpec
from ai_delivery_agent.utils.json_utils import extract_json_object


class RequirementAgent:
    name = "requirement_agent"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, requirement: str) -> RequirementSpec:
        if self.llm.enabled:
            system = (
                "You are a senior product-engineering analyst. "
                "Return strict JSON only. No markdown."
            )
            user = f"""
Decompose this requirement into an implementation-ready spec.

Requirement:
{requirement}

Return JSON with exactly these keys:
- pain_point: string
- user_stories: string[]
- acceptance_criteria: string[]
- constraints: string[]
- risks: string[]
""".strip()
            response = self.llm.complete(system, user, max_tokens=1200)
            data = extract_json_object(response.text)
            if data:
                return RequirementSpec(
                    pain_point=str(data.get("pain_point", "")) or self._infer_pain_point(requirement),
                    user_stories=self._list(data.get("user_stories")),
                    acceptance_criteria=self._list(data.get("acceptance_criteria")),
                    constraints=self._list(data.get("constraints")),
                    risks=self._list(data.get("risks")),
                )
        return self._heuristic(requirement)

    def _heuristic(self, requirement: str) -> RequirementSpec:
        clauses = [part.strip() for part in re.split(r"[。.!?；;\n]+", requirement) if part.strip()]
        acceptance = clauses[:5] or [requirement.strip()]
        return RequirementSpec(
            pain_point=self._infer_pain_point(requirement),
            user_stories=[
                "As an engineer, I want the requirement converted into concrete code changes so that implementation work is less ambiguous.",
                "As a reviewer, I want generated changes to include verification guidance so that review risk is controlled.",
            ],
            acceptance_criteria=acceptance,
            constraints=[
                "Do not introduce unnecessary dependencies.",
                "Preserve the existing project structure and coding style.",
                "Generate a reviewable diff instead of directly mutating code by default.",
            ],
            risks=[
                "The requirement may be underspecified.",
                "Generated code may miss hidden business rules not present in the repository.",
                "Tests must be reviewed before merging.",
            ],
        )

    @staticmethod
    def _infer_pain_point(requirement: str) -> str:
        return (
            "Manual translation from requirement to code is slow and error-prone; "
            f"this run attempts to convert the requirement into a planned, testable code change: {requirement}"
        )

    @staticmethod
    def _list(value: object) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
