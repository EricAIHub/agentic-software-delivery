from pathlib import Path

from ai_delivery_agent.utils.file_utils import scan_repo


def test_scan_repo_loads_python_file(tmp_path: Path):
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    snapshot = scan_repo(str(tmp_path), max_files=5, max_file_bytes=1000)
    assert snapshot.stats["loaded_files"] == 1
    assert snapshot.files[0].path == "app.py"
