from __future__ import annotations

from src.converter.schema import normalize_context
from src.generators.renderers import (
    section,
    build_git_rules,
    build_versioning_rules,
    build_dependency_and_ignore_rules,
    DEFAULT_WORKFLOW,
)


def compose_prompt(
    context_data: dict,
    target_agent: str,
) -> str:
    """
    Directly converts normalized context data into a copy-ready Technical English prompt.
    """
    data = normalize_context(context_data)
    is_antigravity = (target_agent.lower() == "antigravity")

    parts = []
    if is_antigravity:
        parts.append("# Instruction Prompt (Antigravity)")

        # Goal/Task
        parts.append(section("Goal", data["goal"]))
        parts.append(section("Background Context", data["context"] + data["project"]))
        parts.append(section("Scope & Constraints", data["files"] + data["constraints"]))
        parts.append(section("Forbidden", data["forbidden"]))

        git_rules = build_git_rules(data["git_rules"])
        if git_rules:
            parts.append(section("Git Rules", git_rules))

        version_rules = build_versioning_rules(data["versioning_rules"])
        if version_rules:
            parts.append(section("Versioning Rules", version_rules))

        dep_and_ignore = build_dependency_and_ignore_rules(data["dependency_rules"], data["ignore_rules"])
        if dep_and_ignore:
            parts.append(section("Dependency and Ignore Rules", dep_and_ignore))

        parts.append(section("Verification", data["verification"]))
    else:
        parts.append("# Instruction Prompt (Codex)")

        # Goal/Task
        parts.append(section("Goal", data["goal"]))
        parts.append(section("Context / Background", data["context"] + data["project"]))
        parts.append(section("Constraints", data["constraints"]))
        parts.append(section("Forbidden", data["forbidden"]))

        git_rules = build_git_rules(data["git_rules"])
        if git_rules:
            parts.append(section("Git Rules", git_rules))

        version_rules = build_versioning_rules(data["versioning_rules"])
        if version_rules:
            parts.append(section("Versioning Rules", version_rules))

        dep_and_ignore = build_dependency_and_ignore_rules(data["dependency_rules"], data["ignore_rules"])
        if dep_and_ignore:
            parts.append(section("Dependency and Ignore Rules", dep_and_ignore))

        parts.append(section("Verification", data["verification"]))
        parts.append(section("Output Format", data["output_format"]))

    return "\n\n".join(p for p in parts if p).strip() + "\n"
