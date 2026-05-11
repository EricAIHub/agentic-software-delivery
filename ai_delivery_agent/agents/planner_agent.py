from __future__ import annotations

import re
from typing import List

from ai_delivery_agent.llm import LLMClient
from ai_delivery_agent.models import ImplementationPlan, RepoSnapshot, RequirementSpec


class PlannerAgent:
    name = "planner_agent"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, requirement: str, spec: RequirementSpec, repo: RepoSnapshot) -> ImplementationPlan:
        selected = self._select_relevant_files(requirement, repo)

        if self.llm.enabled:
            system = (
                "You are a staff software engineer. Produce a concise implementation plan. "
                "Do not write code yet."
            )
            user = f"""
Requirement:
{requirement}

Requirement spec:
{spec.model_dump_json(indent=2)}

Repository tree:
{repo.tree}

Loaded files:
{chr(10).join(f'- {file.path} ({file.language}, {file.size_bytes} bytes)' for file in repo.files)}

Likely relevant files selected by heuristic:
{chr(10).join(f'- {path}' for path in selected) or '- none'}

Write a markdown implementation plan with:
1. Files to inspect/change
2. Code changes
3. Data/API compatibility concerns
4. Test strategy
5. Rollback risk
""".strip()
            response = self.llm.complete(system, user, max_tokens=1800)
            if response.text and not response.used_mock:
                return ImplementationPlan(selected_files=selected, plan_markdown=response.text.strip())

        plan = self._heuristic_plan(requirement, spec, repo, selected)
        return ImplementationPlan(selected_files=selected, plan_markdown=plan)

    def _select_relevant_files(self, requirement: str, repo: RepoSnapshot) -> List[str]:
        keywords = self._keywords(requirement)
        scores = []
        for file in repo.files:
            haystack = f"{file.path}\n{file.content[:4000]}".lower()
            score = sum(1 for keyword in keywords if keyword in haystack)
            if self._looks_like_entrypoint(file.path):
                score += 2
            if self._looks_like_test(file.path):
                score += 1
            if score > 0:
                scores.append((score, file.path))
        scores.sort(key=lambda item: (-item[0], item[1]))
        selected = [path for _, path in scores[:8]]
        if selected:
            return selected
        return [file.path for file in repo.files[: min(5, len(repo.files))]]

    @staticmethod
    def _keywords(requirement: str) -> List[str]:
        words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}|/[a-zA-Z0-9_/-]+", requirement.lower())
        normalized = set(words)
        for token in requirement.lower().replace("-", " ").replace("_", " ").split():
            if len(token) >= 3:
                normalized.add(token.strip("'\"`.,:;()[]{}"))
        return [word for word in normalized if word]

    @staticmethod
    def _looks_like_entrypoint(path: str) -> bool:
        lowered = path.lower()
        names = ("main.py", "app.py", "server.py", "index.js", "index.ts", "routes", "controller")
        return any(name in lowered for name in names)

    @staticmethod
    def _looks_like_test(path: str) -> bool:
        lowered = path.lower()
        return "test" in lowered or "spec" in lowered

    @staticmethod
    def _heuristic_plan(
        requirement: str,
        spec: RequirementSpec,
        repo: RepoSnapshot,
        selected_files: List[str],
    ) -> str:
        selected_text = "\n".join(f"- `{path}`" for path in selected_files) or "- No file loaded. Increase max_files."
        criteria = "\n".join(f"- {item}" for item in spec.acceptance_criteria)
        return f"""# Implementation Plan

## Requirement

{requirement}

## Core pain point

{spec.pain_point}

## Candidate files

{selected_text}

## Proposed engineering path

1. Inspect the selected entrypoint, route, service, and test files.
2. Make the smallest code change that satisfies the acceptance criteria.
3. Preserve existing public interfaces unless the requirement explicitly asks for an API change.
4. Add or update tests near the affected code path.
5. Review the patch for security, compatibility, and regression risk before applying.

## Acceptance criteria

{criteria}

## Repository stats

```json
{repo.stats}
```
""".strip()
