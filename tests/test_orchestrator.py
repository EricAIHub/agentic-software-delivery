from pathlib import Path

from ai_delivery_agent.orchestrator import DeliveryOrchestrator


def test_orchestrator_mock_run(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    output = tmp_path / "run"

    result = DeliveryOrchestrator().run(
        repo_path=str(repo),
        requirement="Add health check behavior",
        output_dir=str(output),
        dry_run=True,
    )

    assert result.proposed_patch.valid_unified_diff
    assert (output / "04_patch.diff").exists()
    assert "health" in result.requirement.lower()
