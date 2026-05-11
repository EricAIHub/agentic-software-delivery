from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Iterable, List

from ai_delivery_agent.models import FileSnapshot, RepoSnapshot

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "target",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "env",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".kt",
    ".swift",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".env.example",
    ".dockerfile",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".md": "Markdown",
    ".txt": "Text",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
}


def scan_repo(repo_path: str, max_files: int, max_file_bytes: int) -> RepoSnapshot:
    root = Path(repo_path).expanduser().resolve()
    files: List[FileSnapshot] = []
    tree_paths: List[str] = []

    for path in _iter_files(root):
        relative = path.relative_to(root).as_posix()
        tree_paths.append(relative)
        if len(files) >= max_files:
            continue
        if not _is_text_candidate(path):
            continue
        try:
            size_bytes = path.stat().st_size
        except OSError:
            continue
        if size_bytes > max_file_bytes:
            continue
        content = _read_text(path)
        if content is None:
            continue
        files.append(
            FileSnapshot(
                path=relative,
                language=_language(path),
                size_bytes=size_bytes,
                content=content,
            )
        )

    language_counts = Counter(file.language for file in files)
    stats = {
        "total_visible_files": len(tree_paths),
        "loaded_files": len(files),
        "languages": dict(language_counts),
    }
    tree = _render_tree(tree_paths)
    return RepoSnapshot(root=str(root), tree=tree, stats=stats, files=files)


def _iter_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in IGNORE_DIRS]
        current_path = Path(current_root)
        for filename in sorted(filenames):
            path = current_path / filename
            if path.is_file():
                yield path


def _is_text_candidate(path: Path) -> bool:
    if path.name in {"Dockerfile", "Makefile", "README", "LICENSE"}:
        return True
    suffixes = path.suffixes
    if path.name == ".env.example":
        return True
    if not suffixes:
        return False
    return suffixes[-1].lower() in TEXT_EXTENSIONS


def _read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1")
        except UnicodeDecodeError:
            return None


def _language(path: Path) -> str:
    if path.name == "Dockerfile":
        return "Dockerfile"
    if path.name == "Makefile":
        return "Makefile"
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "Text")


def _render_tree(paths: List[str]) -> str:
    max_paths = 300
    shown = sorted(paths)[:max_paths]
    suffix = "" if len(paths) <= max_paths else f"\n... {len(paths) - max_paths} more files"
    return "\n".join(shown) + suffix
