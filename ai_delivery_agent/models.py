from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class RunRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the target repository")
    requirement: str = Field(..., min_length=3, description="Product or engineering requirement")
    max_files: int = Field(20, ge=1, le=80, description="Maximum files to load into context")
    dry_run: bool = Field(True, description="If true, do not apply generated patch")

    @field_validator("repo_path")
    @classmethod
    def repo_path_must_exist(cls, value: str) -> str:
        path = Path(value).expanduser()
        if not path.exists():
            raise ValueError(f"repo_path does not exist: {value}")
        if not path.is_dir():
            raise ValueError(f"repo_path must be a directory: {value}")
        return str(path)


class FileSnapshot(BaseModel):
    path: str
    language: str
    size_bytes: int
    content: str


class RepoSnapshot(BaseModel):
    root: str
    tree: str
    stats: Dict[str, Any]
    files: List[FileSnapshot]


class RequirementSpec(BaseModel):
    pain_point: str
    user_stories: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class ImplementationPlan(BaseModel):
    selected_files: List[str] = Field(default_factory=list)
    plan_markdown: str


class PatchResult(BaseModel):
    patch: str
    valid_unified_diff: bool
    apply_attempted: bool = False
    apply_succeeded: bool = False
    apply_message: str = ""


class DeliveryResult(BaseModel):
    requirement: str
    run_dir: str
    requirement_spec: RequirementSpec
    repo_stats: Dict[str, Any]
    selected_files: List[str]
    proposed_patch: PatchResult
    test_plan: str
    review: str
    artifacts: Dict[str, str]
