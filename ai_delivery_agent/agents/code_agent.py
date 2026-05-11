from __future__ import annotations

from typing import List

from ai_delivery_agent.config import Settings
from ai_delivery_agent.llm import LLMClient
from ai_delivery_agent.models import ImplementationPlan, RepoSnapshot
from ai_delivery_agent.utils.diff_utils import extract_diff, make_new_file_patch


class CodeAgent:
    name = "code_agent"

    def __init__(self, llm: LLMClient, settings: Settings):
        self.llm = llm
        self.settings = settings

    def run(self, requirement: str, plan: ImplementationPlan, repo: RepoSnapshot) -> str:
        selected_files = self._files_by_path(repo, plan.selected_files)
        context = self._format_file_context(selected_files)

        if self.llm.enabled:
            system = (
                "You are a senior software engineer generating a safe code patch. "
                "Return ONLY a unified diff. No markdown fences, no explanation. "
                "Use paths relative to the repository root. "
                "Do not modify files that are not necessary. "
                "Do not invent dependencies unless unavoidable."
            )
            user = f"""
Requirement:
{requirement}

Implementation plan:
{plan.plan_markdown}

Relevant repository files:
{context}

Generate a unified diff that implements the requirement.
""".strip()
            response = self.llm.complete(system, user, max_tokens=3000)
            diff = extract_diff(response.text)
            if diff:
                return diff

        return self._mock_patch(requirement, plan)

    def _files_by_path(self, repo: RepoSnapshot, paths: List[str]):
        wanted = set(paths)
        return [file for file in repo.files if file.path in wanted]

    def _format_file_context(self, files) -> str:
        chunks = []
        total = 0
        for file in files:
            header = f"\n--- FILE: {file.path} ({file.language}) ---\n"
            content = file.content
            remaining = self.settings.max_context_chars - total - len(header)
            if remaining <= 0:
                break
            if len(content) > remaining:
                content = content[:remaining] + "\n# ... truncated ...\n"
            chunks.append(header + content)
            total += len(header) + len(content)
        return "\n".join(chunks) if chunks else "No file context available."

    @staticmethod
    def _mock_patch(requirement: str, plan: ImplementationPlan) -> str:
        content = f"""# Agent-generated implementation brief

This repository was processed in mock mode because no working LLM API key was configured.

## Requirement

{requirement}

## Selected files

{chr(10).join(f'- {path}' for path in plan.selected_files) or '- none'}

## Next action

Set OPENAI_API_KEY and rerun the command to generate a repository-specific code diff.

## Plan snapshot

{plan.plan_markdown}
""".strip()
        return make_new_file_patch("agent_output/IMPLEMENTATION_PLAN.md", content)
