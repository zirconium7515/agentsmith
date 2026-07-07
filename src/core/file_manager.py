from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "data",
    "raw",
    "backup",
    "archive",
    "dist",
    "build",
    ".cache",
}

EXCLUDED_FILES_AND_PATTERNS = {
    "AGENTS.md",
    "CONTEXT.compact.md",
    "CONTEXT_FOR_AI.md",
    "CONTEXT_FOR_ANTIGRAVITY.md",
    "COPY_READY_PROMPT.md",
    "TASK.md",
    "implementation_plan.md",
    "walkthrough.md",
}

EXCLUDED_PATHS = [
    os.path.normpath("results/raw"),
]


def is_excluded(path: str, base_path: str) -> bool:
    rel_path = os.path.relpath(path, base_path)
    if rel_path == ".":
        return False

    parts = Path(rel_path).parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True

    normalized_rel = os.path.normpath(rel_path)
    filename = os.path.basename(normalized_rel)
    if filename in EXCLUDED_FILES_AND_PATTERNS:
        return True

    if normalized_rel.startswith(os.path.normpath(".agents/AGENTS.md")) or normalized_rel.startswith(os.path.normpath(".agents/skills")):
        return True

    return any(
        normalized_rel == excluded or normalized_rel.startswith(excluded + os.sep)
        for excluded in EXCLUDED_PATHS
    )


def read_file(filepath: str) -> Optional[str]:
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as exc:
        print(f"Error reading {filepath}: {exc}")
        return None


def write_file(filepath: str, content: str) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
        return True
    except Exception as exc:
        print(f"Error writing {filepath}: {exc}")
        return False


def generate_project_tree(root_dir: str) -> str:
    """Generate a compact ASCII project tree while skipping risky folders."""
    tree_lines = [os.path.basename(root_dir.rstrip(os.sep)) + "/"]

    def walk_dir(current_dir: str, prefix: str = "") -> None:
        try:
            items = sorted(os.listdir(current_dir), key=str.lower)
        except PermissionError:
            return

        filtered_items = [
            item
            for item in items
            if not is_excluded(os.path.join(current_dir, item), root_dir)
        ]

        for index, item in enumerate(filtered_items):
            full_path = os.path.join(current_dir, item)
            is_last = index == len(filtered_items) - 1
            connector = "`-- " if is_last else "|-- "
            tree_lines.append(f"{prefix}{connector}{item}")

            if os.path.isdir(full_path):
                extension = "    " if is_last else "|   "
                walk_dir(full_path, prefix + extension)

    walk_dir(root_dir)
    return "\n".join(tree_lines)
