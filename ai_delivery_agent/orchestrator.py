from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from ai_delivery_agent.agents.code_agent import CodeAgent
from ai_delivery_agent.agents.planner_agent import PlannerAgent
from ai_delivery_agent.agents.repo_agent import RepoScannerAgent
from ai_delivery_agent.agents.requirement_agent import RequirementAgent
from ai_delivery_agent.agents.review_agent import ReviewAgent
from ai_delivery_agent.agents.test_agent import TestAgent
from ai_delivery_agent.config import Settings, get_settings
from ai_delivery_agent.llm import LLMClient
from ai_delivery_agent.models import DeliveryResult, PatchResult
from ai_delivery_agent.utils.diff_utils import git_apply, git_apply_check, is_unified_diff


class DeliveryOrchestrator:
    """Coordinates the multi-agent workflow."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.llm = LLMClient(self.settings)
        self.requirement_agent = RequirementAgent(self.llm)
        self.repo_agent = RepoScannerAgent(self.settings)
        self.planner_agent = PlannerAgent(self.llm)
        self.code_agent = CodeAgent(self.llm, self.settings)
        self.test_agent = TestAgent(self.llm)
        self.review_agent = ReviewAgent(self.llm)

    def run(
        self,
        *,
        repo_path: str,
        requirement: str,
        max_files: int = 20,
        dry_run: bool = True,
        output_dir: Optional[str] = None,
    ) -> DeliveryResult:
        run_dir = self._make_run_dir(output_dir)

        requirement_spec = self.requirement_agent.run(requirement)
        repo_snapshot = self.repo_agent.run(repo_path=repo_path, max_files=max_files)
        plan = self.planner_agent.run(requirement=requirement, spec=requirement_spec, repo=repo_snapshot)
        patch = self.code_agent.run(requirement=requirement, plan=plan, repo=repo_snapshot)

        valid_diff = is_unified_diff(patch)
        apply_attempted = False
        apply_succeeded = False
        apply_message = ""

        if valid_diff:
            check_succeeded, check_message = git_apply_check(repo_path, patch)
            apply_message = f"git apply --check: {check_message}"
            if not dry_run:
                apply_attempted = True
                if check_succeeded:
                    apply_succeeded, apply_message = git_apply(repo_path, patch)
                else:
                    apply_succeeded = False
            else:
                apply_attempted = False
        else:
            apply_message = "No valid unified diff generated."

        patch_result = PatchResult(
            patch=patch,
            valid_unified_diff=valid_diff,
            apply_attempted=apply_attempted,
            apply_succeeded=apply_succeeded,
            apply_message=apply_message,
        )

        test_plan = self.test_agent.run(
            requirement=requirement,
            spec=requirement_spec,
            plan=plan,
            patch=patch,
        )
        review = self.review_agent.run(
            requirement=requirement,
            spec=requirement_spec,
            plan=plan,
            patch_result=patch_result,
            test_plan=test_plan,
        )

        artifacts = self._write_artifacts(
            run_dir=run_dir,
            requirement_spec=requirement_spec.model_dump(),
            repo_summary={"root": repo_snapshot.root, "tree": repo_snapshot.tree, "stats": repo_snapshot.stats},
            plan=plan.plan_markdown,
            patch=patch,
            test_plan=test_plan,
            review=review,
        )

        result = DeliveryResult(
            requirement=requirement,
            run_dir=str(run_dir),
            requirement_spec=requirement_spec,
            repo_stats=repo_snapshot.stats,
            selected_files=plan.selected_files,
            proposed_patch=patch_result,
            test_plan=test_plan,
            review=review,
            artifacts=artifacts,
        )

        result_path = run_dir / "result.json"
        result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        result.artifacts["result"] = str(result_path)
        return result

    def _make_run_dir(self, output_dir: Optional[str]) -> Path:
        if output_dir:
            run_dir = Path(output_dir).expanduser().resolve()
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            run_dir = self.settings.runs_dir_path / f"run-{timestamp}-{uuid4().hex[:8]}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    @staticmethod
    def _write_artifacts(
        *,
        run_dir: Path,
        requirement_spec: Dict,
        repo_summary: Dict,
        plan: str,
        patch: str,
        test_plan: str,
        review: str,
    ) -> Dict[str, str]:
        artifacts = {
            "requirement": run_dir / "01_requirement.json",
            "repo_summary": run_dir / "02_repo_summary.json",
            "plan": run_dir / "03_plan.md",
            "patch": run_dir / "04_patch.diff",
            "test_plan": run_dir / "05_test_plan.md",
            "review": run_dir / "06_review.md",
        }
        artifacts["requirement"].write_text(json.dumps(requirement_spec, indent=2), encoding="utf-8")
        artifacts["repo_summary"].write_text(json.dumps(repo_summary, indent=2), encoding="utf-8")
        artifacts["plan"].write_text(plan, encoding="utf-8")
        artifacts["patch"].write_text(patch, encoding="utf-8")
        artifacts["test_plan"].write_text(test_plan, encoding="utf-8")
        artifacts["review"].write_text(review, encoding="utf-8")
        return {key: str(path) for key, path in artifacts.items()}
