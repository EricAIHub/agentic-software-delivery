from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Tuple


def extract_diff(text: str) -> str:
    """Extract a unified diff from plain text or a fenced code block."""
    text = text.strip()
    if not text:
        return ""

    if "```diff" in text:
        start = text.find("```diff") + len("```diff")
        end = text.find("```", start)
        return text[start:end].strip() if end != -1 else text[start:].strip()

    if "```" in text:
        start = text.find("```") + len("```")
        first_newline = text.find("\n", start)
        if first_newline != -1:
            start = first_newline + 1
        end = text.find("```", start)
        candidate = text[start:end].strip() if end != -1 else text[start:].strip()
        if is_unified_diff(candidate):
            return candidate

    if is_unified_diff(text):
        return text

    return ""


def is_unified_diff(patch: str) -> bool:
    patch = patch.strip()
    if not patch:
        return False
    has_file_marker = ("diff --git " in patch) or ("--- " in patch and "+++ " in patch)
    has_hunk = "@@" in patch
    return has_file_marker and has_hunk


def git_apply_check(repo_path: str, patch: str) -> Tuple[bool, str]:
    return _git_apply(repo_path=repo_path, patch=patch, check_only=True)


def git_apply(repo_path: str, patch: str) -> Tuple[bool, str]:
    return _git_apply(repo_path=repo_path, patch=patch, check_only=False)


def _git_apply(repo_path: str, patch: str, check_only: bool) -> Tuple[bool, str]:
    repo = Path(repo_path).expanduser().resolve()
    if not is_unified_diff(patch):
        return False, "Patch is not a valid unified diff."

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".diff", delete=False) as tmp:
        tmp.write(patch)
        tmp_path = tmp.name

    args = ["git", "apply"]
    if check_only:
        args.append("--check")
    args.append(tmp_path)

    try:
        completed = subprocess.run(
            args,
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return False, "git is not installed or is not available on PATH."
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    message = (completed.stdout + "\n" + completed.stderr).strip()
    if completed.returncode == 0:
        return True, message or "git apply succeeded."
    return False, message or f"git apply failed with exit code {completed.returncode}."


def make_new_file_patch(relative_path: str, content: str) -> str:
    """Create a simple unified diff that adds a new text file."""
    lines = content.splitlines()
    body = "\n".join(f"+{line}" for line in lines)
    if body:
        body += "\n"
    return (
        f"diff --git a/{relative_path} b/{relative_path}\n"
        "new file mode 100644\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        f"+++ b/{relative_path}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}"
    )
