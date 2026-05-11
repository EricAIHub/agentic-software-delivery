from __future__ import annotations

from ai_delivery_agent.config import Settings
from ai_delivery_agent.models import RepoSnapshot
from ai_delivery_agent.utils.file_utils import scan_repo


class RepoScannerAgent:
    name = "repo_scanner_agent"

    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self, repo_path: str, max_files: int) -> RepoSnapshot:
        return scan_repo(
            repo_path=repo_path,
            max_files=max_files,
            max_file_bytes=self.settings.max_file_bytes,
        )
