from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai_delivery_agent.orchestrator import DeliveryOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI Delivery Agent MVP.")
    parser.add_argument("--repo", required=True, help="Path to the target repository")
    parser.add_argument("--requirement", required=True, help="Requirement to implement")
    parser.add_argument("--max-files", type=int, default=20, help="Maximum files to load into context")
    parser.add_argument("--output", default=None, help="Output directory for run artifacts")
    parser.add_argument("--apply", action="store_true", help="Apply the generated patch with git apply")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).expanduser()
    if not repo.exists() or not repo.is_dir():
        print(f"Repository path is invalid: {args.repo}", file=sys.stderr)
        return 2

    orchestrator = DeliveryOrchestrator()
    result = orchestrator.run(
        repo_path=str(repo),
        requirement=args.requirement,
        max_files=args.max_files,
        dry_run=not args.apply,
        output_dir=args.output,
    )

    summary = {
        "run_dir": result.run_dir,
        "selected_files": result.selected_files,
        "valid_unified_diff": result.proposed_patch.valid_unified_diff,
        "apply_attempted": result.proposed_patch.apply_attempted,
        "apply_succeeded": result.proposed_patch.apply_succeeded,
        "apply_message": result.proposed_patch.apply_message,
        "artifacts": result.artifacts,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
