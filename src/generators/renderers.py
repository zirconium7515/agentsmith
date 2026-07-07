from __future__ import annotations

from src.converter.schema import empty_context, estimate_tokens, normalize_context


def bullets(items: list[str], fallback: str | None = None) -> str:
    if not items:
        return fallback or ""
    return "\n".join(f"- {item}" for item in items)


def section(title: str, items: list[str], fallback: str | None = None) -> str:
    if not items:
        if fallback is None:
            return ""
        return f"## {title}\n{fallback}"
    return f"## {title}\n" + bullets(items)


DEFAULT_WORKFLOW = [
    "Source of truth: Windows Google Drive mirrored or streamed workspace.",
    "Active development happens in the Google Drive workspace through Windows File Explorer.",
    "GitHub is used for backup, version tracking, deployment, and distribution.",
    "Runtime machines update through `git pull`.",
    "Do not treat runtime folders as the source of truth.",
    "Do not suggest clone or worktree alternatives.",
]


def deduplicate_workflow(custom_workflow: list[str]) -> list[str]:
    cleaned = []
    for bullet in custom_workflow:
        lower = bullet.lower()
        if any(kw in lower for kw in ["source of truth", "google drive", "googledrive", "file explorer", "github", "git pull", "clone", "worktree"]):
            continue
        cleaned.append(bullet)
    return cleaned


def build_git_rules(custom_git_rules: list[str]) -> list[str]:
    if not custom_git_rules:
        return []
    rules_list = []
    has_push = any("push" in r.lower() for r in custom_git_rules)
    has_version = any("version" in r.lower() or "v" in r.lower() for r in custom_git_rules)
    has_commit = any("commit" in r.lower() for r in custom_git_rules)

    if has_push:
        rules_list.append("Push developed code to GitHub.")
    if has_version:
        rules_list.append("Follow the `vX.Y.Z` versioning rule before pushing.")
    if has_commit:
        rules_list.append("Include the version in the commit message.")
    
    rules_list.append("Do not commit or push automatically unless explicitly requested.")
    
    for r in custom_git_rules:
        r_lower = r.lower()
        if any(x in r_lower for x in ["push developed code", "follow the", "include the version in the commit", "automatically unless"]):
            continue
        rules_list.append(r)
    return rules_list


def build_versioning_rules(custom_versioning: list[str]) -> list[str]:
    if not custom_versioning:
        return []
    rules_list = [
        "Use version format `vX.Y.Z`.",
        "Increment `X` for large-scale patches.",
        "Increment `Y` for major feature additions or redesigns within the same `X` version.",
        "Increment `Z` for small feature patches, bug fixes, or minor maintenance patches within the same `Y` version.",
    ]
    for r in custom_versioning:
        r_lower = r.lower()
        if any(x in r_lower for x in ["version format", "increment `x`", "increment `y`", "increment `z`"]):
            continue
        if "기준" in r or "표시한다" in r or "인덱스" in r or "맞춰서" in r:
            continue
        rules_list.append(r)
    return rules_list


def build_dependency_and_ignore_rules(dependency_rules: list[str], ignore_rules: list[str]) -> list[str]:
    combined = dependency_rules + ignore_rules
    if not combined:
        return []
    rules_list = []
    has_venv = any("venv" in r.lower() or "gitignore" in r.lower() for r in combined)
    if has_venv:
        rules_list.append("Add virtual environments such as `venv/` to `.gitignore`.")
        rules_list.append("Do not manage heavy runtime or generated folders as source files in the Google Drive workspace.")
    
    for r in combined:
        r_lower = r.lower()
        if any(x in r_lower for x in ["add virtual environments", "do not manage heavy"]):
            continue
        rules_list.append(r)
    return rules_list


def render_compact_context(context_data: dict) -> str:
    data = normalize_context(context_data)
    dep_and_ignore = build_dependency_and_ignore_rules(data["dependency_rules"], data["ignore_rules"])
    parts = [
        "# Compact Context",
        section("Project", data["project"]),
        section("Goal", data["goal"]),
        section("Context", data["context"]),
        section("Environment", data["environment"]),
        section(
            "Workflow",
            DEFAULT_WORKFLOW + deduplicate_workflow(data["workflow"]),
        ),
        section("Git Rules", build_git_rules(data["git_rules"])),
        section("Versioning Rules", build_versioning_rules(data["versioning_rules"])),
        section("Dependency and Ignore Rules", dep_and_ignore),
        section(
            "Agent Rules",
            [
                "Make minimal focused changes.",
                "Avoid unrelated refactoring.",
                "Preserve existing file paths and output naming conventions.",
            ]
            + data["rules"],
        ),
        section("Constraints", data["constraints"]),
        section("Forbidden Actions", data["forbidden"]),
        section("Relevant Files", data["files"]),
        section(
            "Verification",
            [
                "Run the smallest relevant test or startup command.",
                "Report changed files and commands run.",
            ]
            + data["verification"],
        ),
        section("Output Format", data["output_format"]),
        section("Warnings", data["warnings"]),
    ]
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def render_codex_agents(context_data: dict) -> str:
    data = normalize_context(context_data)
    parts = [
        "# AGENTS.md",
        section(
            "Project Workflow",
            DEFAULT_WORKFLOW + deduplicate_workflow(data["workflow"]),
        ),
    ]
    
    git_rules = build_git_rules(data["git_rules"])
    if git_rules:
        parts.append(section("Git Rules", git_rules))
        
    version_rules = build_versioning_rules(data["versioning_rules"])
    if version_rules:
        parts.append(section("Versioning Rules", version_rules))
        
    dep_and_ignore = build_dependency_and_ignore_rules(data["dependency_rules"], data["ignore_rules"])
    if dep_and_ignore:
        parts.append(section("Dependency and Ignore Rules", dep_and_ignore))

    parts.extend([
        section(
            "Editing Rules",
            [
                "Make minimal, focused changes.",
                "Inspect relevant files before editing.",
                "Do not refactor unrelated code.",
                "Do not rename files, folders, public functions, config keys, or output columns unless explicitly requested.",
                "Preserve existing Korean comments and UI text unless the task is specifically about language cleanup.",
                "Use English for technical identifiers and agent-facing documentation.",
            ]
            + data["rules"],
        ),
        section(
            "Google Drive Safety",
            [
                "Assume files are synchronized by Google Drive.",
                "Avoid rapid mass file creation, deletion, or renaming.",
                "Do not create unnecessary duplicate files.",
                "Do not overwrite large files blindly.",
                "Do not modify Google Drive sync settings.",
                "Do not move the project folder.",
                "If a file conflict or duplicate sync file is detected, report it before editing.",
            ],
        ),
        section(
            "Data Safety",
            [
                "Treat raw experiment data as read-only.",
                "Never delete or overwrite files under `data/`, `raw/`, `backup/`, `archive/`, or `results/raw/`.",
                "Never modify original `.txt`, `.bmp`, `.jpg`, `.png`, `.csv`, or measurement files unless explicitly requested.",
                "Derived outputs must be written only to configured output folders.",
                "Preserve original filenames in output metadata when possible.",
            ],
        ),
        section(
            "Dependency Policy",
            [
                "Do not add dependencies unless necessary.",
            ],
        ),
        section(
            "Verification",
            [
                "After changes, run the smallest relevant verification command.",
                "Prefer `python -m compileall .`, `pytest`, GUI startup checks, or script dry runs when applicable.",
                "If verification cannot be run, explain why.",
            ]
            + data["verification"],
        ),
        section(
            "Final Report Format",
            [
                "root cause",
                "changed files",
                "commands run",
                "verification result",
                "remaining risks",
            ],
        ),
    ])
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def render_codex_task(context_data: dict) -> str:
    data = normalize_context(context_data)
    parts = [
        "# TASK.md",
        "## Fixed Workflow",
        "- Source/development: Google Drive mirrored workspace.",
        "- Backup/deployment: GitHub repository.",
        "- Runtime: local machines pull from GitHub.",
        "- Do not suggest or create a separate clone, worktree, or alternative development structure.",
        "",
        section("Goal", data["goal"], "- (No active task request.)"),
        section("Context", data["context"], "- (No active task request.)"),
        section("Scope", data["files"] + data["constraints"], "- (No active task request.)"),
        section("Current Problem", data["project"], "- (No active task request.)"),
        section("Constraints", data["constraints"], "- (No active task request.)"),
        section("Forbidden", data["forbidden"], "- (No active task request.)"),
        section("Verification", data["verification"], "- (No active task verification defined.)"),
        section(
            "Output",
            data["output_format"]
            or [
                "Explain root cause.",
                "List changed files.",
                "List commands run.",
                "Report verification result.",
            ],
        ),
    ]
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def render_codex_bundle(outputs: dict[str, str], project_tree: str) -> str:
    parts = [
        "Read this document carefully.",
        "Follow AGENTS.md strictly.",
    ]
    if "TASK.md" in outputs:
        parts.append("Complete TASK.md only.")
    else:
        parts.extend([
            "This is project initialization context, not a task request.",
            "Do not perform code edits unless a separate TASK.md is provided.",
        ])
    parts.extend([
        "Use the existing Google Drive -> GitHub -> git pull workflow.",
        "Do not suggest clone or worktree alternatives.",
    ])

    for name in ("AGENTS.md", "CONTEXT.compact.md", "TASK.md"):
        if name in outputs:
            parts.extend(["", "========================================", f"# {name}", "", outputs[name].strip()])

    if project_tree:
        parts.extend(["", "========================================", "# Project Tree", "", f"```\n{project_tree}\n```"])

    return "\n".join(parts).strip() + "\n"


def render_antigravity_agents(context_data: dict) -> str:
    data = normalize_context(context_data)
    parts = [
        "# AGENTS.md",
        section(
            "Project Workflow",
            [
                "Apply these rules only to this workspace.",
            ]
            + DEFAULT_WORKFLOW
            + deduplicate_workflow(data["workflow"]),
        ),
    ]
    
    git_rules = build_git_rules(data["git_rules"])
    if git_rules:
        parts.append(section("Git Rules", git_rules))
        
    version_rules = build_versioning_rules(data["versioning_rules"])
    if version_rules:
        parts.append(section("Versioning Rules", version_rules))
        
    dep_and_ignore = build_dependency_and_ignore_rules(data["dependency_rules"], data["ignore_rules"])
    if dep_and_ignore:
        parts.append(section("Dependency and Ignore Rules", dep_and_ignore))

    parts.extend([
        section(
            "Editing Rules",
            [
                "Keep planning artifacts separate from source code.",
                "Use `.agents/AGENTS.md` for project-specific rules.",
                "Use `skills/<skill_name>/SKILL.md` for reusable workflows only when needed.",
                "Use `implementation_plan.md` for approved implementation plans.",
                "Use `task.md` for live task checklist state.",
                "Use `walkthrough.md` for the final implementation and verification summary.",
                "Put one-off debug scripts or temporary parsing files under the conversation `scratch/` area, not the source tree.",
                "Use GitHub-style alerts, Mermaid diagrams, and diff blocks when they improve review clarity.",
                "Make minimal, focused changes.",
                "Inspect relevant files before editing.",
                "Do not refactor unrelated code.",
                "Do not rename files, folders, public functions, config keys, or output columns unless explicitly requested.",
                "Preserve existing Korean comments and UI text unless the task is specifically about language cleanup.",
                "Use English for technical identifiers and agent-facing documentation.",
            ]
            + data["rules"],
        ),
        section(
            "Google Drive Safety",
            [
                "Assume files are synchronized by Google Drive.",
                "Avoid rapid mass file creation, deletion, or renaming.",
                "Do not create unnecessary duplicate files.",
                "Do not overwrite large files blindly.",
                "Do not modify Google Drive sync settings.",
                "Do not move the project folder.",
                "If a file conflict or duplicate sync file is detected, report it before editing.",
            ],
        ),
        section(
            "Data Safety",
            [
                "Treat raw experiment data as read-only.",
                "Never delete or overwrite files under `data/`, `raw/`, `backup/`, `archive/`, or `results/raw/`.",
                "Never modify original `.txt`, `.bmp`, `.jpg`, `.png`, `.csv`, or measurement files unless explicitly requested.",
                "Derived outputs must be written only to configured output folders.",
                "Preserve original filenames in output metadata when possible.",
            ],
        ),
        section(
            "Dependency Policy",
            [
                "Do not add dependencies unless necessary.",
            ],
        ),
        section(
            "Verification",
            [
                "Run the smallest relevant verification command.",
                "Include command output summaries in `walkthrough.md`.",
                "Prefer `python -m compileall .`, `pytest`, GUI startup checks, or script dry runs when applicable.",
                "If verification cannot be run, explain why.",
            ]
            + data["verification"],
        ),
        section(
            "Final Report Format",
            [
                "root cause",
                "changed files",
                "commands run",
                "verification result",
                "remaining risks",
            ],
        ),
    ])
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def render_implementation_plan(context_data: dict) -> str:
    data = normalize_context(context_data)
    parts = [
        "# Implementation Plan",
        "> [!IMPORTANT]",
        "> Do not modify code until the user approves this plan.",
        section("Goal", data["goal"], "- (No active task request.)"),
        section("Background", data["context"] + data["project"], "- (No active task request.)"),
        section("Constraints", data["constraints"], "- (No active task request.)"),
        section("Forbidden Actions", data["forbidden"], "- (No active task request.)"),
        section("Files To Inspect", data["files"], "- (No active task request.)"),
        "## Proposed Changes",
        "- Identify the smallest implementation path after inspecting the relevant files.",
        "- Keep changes scoped to the approved task.",
        "- Preserve existing project workflow and file structure.",
        section("Verification Plan", data["verification"], "- (No active task verification defined.)"),
    ]
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def render_antigravity_task(context_data: dict) -> str:
    data = normalize_context(context_data)
    initial_goal = data["goal"][0] if data["goal"] else "(No active task request.)"
    parts = [
        "# Task",
        f"- [ ] {initial_goal}",
        "- [ ] Inspect project structure and relevant files.",
        "- [ ] Draft or update `implementation_plan.md`.",
        "- [ ] Wait for user approval before code edits when planning is required.",
        "- [ ] Apply approved changes.",
        "- [ ] Run verification.",
        "- [ ] Write `walkthrough.md` with changed files, commands, results, and risks.",
    ]
    return "\n".join(parts).strip() + "\n"


def render_walkthrough(context_data: dict) -> str:
    data = normalize_context(context_data)
    parts = [
        "# Walkthrough",
        "## Summary",
        "- Pending implementation.",
        section("Expected Goal", data["goal"], "- (No active task request.)"),
        "## Changed Files",
        "- Pending.",
        "## Verification",
        "- Pending.",
        "## Remaining Risks",
        bullets(data["warnings"], "- Pending."),
    ]
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def render_antigravity_bundle(outputs: dict[str, str], project_tree: str) -> str:
    parts = [
        "Use these artifacts for Google Antigravity.",
        "Keep planning, task state, and walkthrough documents separate.",
    ]
    if "task.md" in outputs:
        parts.append("Do not modify code until the implementation plan is approved when planning mode is requested.")
    else:
        parts.extend([
            "This is project initialization context, not a task request.",
            "Do not perform code edits unless a separate task.md is provided.",
        ])

    for name in (
        ".agents/AGENTS.md",
        "implementation_plan.md",
        "task.md",
        "walkthrough.md",
        "CONTEXT.compact.md",
    ):
        if name in outputs:
            parts.extend(["", "========================================", f"# {name}", "", outputs[name].strip()])
    if project_tree:
        parts.extend(["", "========================================", "# Project Tree", "", f"```\n{project_tree}\n```"])
    return "\n".join(parts).strip() + "\n"


def build_agent_outputs(
    context_data: dict,
    target_agent: str,
    workflow_mode: str,
    project_tree: str = "",
    include_agents: bool = True,
    include_task: bool = True,
    include_compact: bool = True,
    include_bundle: bool = True,
    raw_text: str = "",
    language_mode: str = "auto",
    prompt_style: str = "balanced",
) -> tuple[dict[str, str], str]:
    data = normalize_context(context_data)
    
    if workflow_mode == "Prompt Only":
        from src.generators.prompt_composer import compose_prompt_only, PromptOnlyConfig
        config = PromptOnlyConfig(
            target_agent="codex" if target_agent.lower() != "antigravity" else "antigravity",
            style=prompt_style,
            language_mode=language_mode,
            allow_llm_fallback=True,
        )
        res = compose_prompt_only(raw_text or "\n".join(data.get("goal", []) + data.get("context", [])), config)
        preview = res.prompt_text
        token_note = f"\n\n---\nEstimated preview tokens: {res.estimated_tokens}\n" if preview else ""
        return {}, preview + token_note

    target = target_agent.lower()
    outputs: dict[str, str] = {}

    is_project_init = (workflow_mode == "Project Init")
    task_data = empty_context() if is_project_init else data

    if target == "antigravity":
        if include_agents:
            outputs[".agents/AGENTS.md"] = render_antigravity_agents(data)
        if include_task:
            outputs["implementation_plan.md"] = render_implementation_plan(task_data)
            outputs["task.md"] = render_antigravity_task(task_data)
            outputs["walkthrough.md"] = render_walkthrough(task_data)
        if include_compact:
            outputs["CONTEXT.compact.md"] = render_compact_context(data)
        if include_bundle:
            outputs["CONTEXT_FOR_ANTIGRAVITY.md"] = render_antigravity_bundle(outputs, project_tree)
            preview_name = "CONTEXT_FOR_ANTIGRAVITY.md"
        else:
            preview_name = next(reversed(outputs), "")
    else:
        if include_agents:
            outputs["AGENTS.md"] = render_codex_agents(data)
        if include_compact:
            outputs["CONTEXT.compact.md"] = render_compact_context(data)
        if include_task:
            outputs["TASK.md"] = render_codex_task(task_data)
        if include_bundle:
            outputs["CONTEXT_FOR_AI.md"] = render_codex_bundle(outputs, project_tree)
            preview_name = "CONTEXT_FOR_AI.md"
        else:
            preview_name = next(reversed(outputs), "")

    if workflow_mode == "Task Prompt" and include_bundle:
        prompt = outputs.get("TASK.md") or outputs.get("implementation_plan.md") or ""
        outputs["COPY_READY_PROMPT.md"] = prompt
        preview_name = "COPY_READY_PROMPT.md"

    preview = outputs.get(preview_name, "")
    token_note = f"\n\n---\nEstimated preview tokens: {estimate_tokens(preview)}\n" if preview else ""
    return outputs, preview + token_note
