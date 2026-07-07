from __future__ import annotations

import json

from src.converter.schema import empty_context, normalize_context

try:
    import ollama
except ImportError:  # pragma: no cover - optional runtime dependency
    ollama = None


PROMPT_TEMPLATE = """
You are AgentSmith's local context compiler.

Convert the user's rough Korean project notes or task request into strict JSON for coding agents.
Optimize for token efficiency and operational clarity.

Rules:
- Remove repetition, emotional background, and conversational filler.
- Preserve exact file paths, commands, tool names, version numbers, and forbidden actions.
- Do not invent facts.
- Use concise Controlled Technical English unless Korean is necessary for domain meaning.
- Separate stable project rules from current task instructions.
- If the input is project initialization context, leave task-specific fields such as `goal` empty unless there is an explicit task request.
- Return JSON only.

Classification Guidelines:
- Development location, source of truth, backup/deployment, and runtime update flow (e.g. git pull) must be placed in `workflow`.
- Commit, push, branch, and commit-message version rules must be placed in `git_rules`.
- `vX.Y.Z`, major/minor/patch, and indexing definitions must be placed in `versioning_rules`.
- Heavy runtime folders (e.g. venv), generated folders, and `.gitignore` rules must be placed in `ignore_rules`.
- Virtual environment setup, pip, dependencies, and packages must be placed in `dependency_rules`.
- Do not put versioning rules under `environment` or generic `constraints`.
- Do not put dependency or `.gitignore` rules under `verification`.
- Do not put stable workflow or project rules under `goal`.

Required schema:
{
  "project": ["short project identity bullets"],
  "goal": ["what the user wants to achieve (leave empty for project initialization context)"],
  "context": ["important background"],
  "environment": ["OS, runtime, dependencies, tools"],
  "workflow": ["development, deployment, update, or collaboration workflow"],
  "rules": ["stable coding or project rules"],
  "git_rules": ["git configuration, push, commit style, branching"],
  "versioning_rules": ["version format (vX.Y.Z) and index definitions"],
  "dependency_rules": ["dependency installation, package managers, virtual environments"],
  "ignore_rules": [".gitignore patterns and heavy folders to skip"],
  "constraints": ["scope limits or conditions"],
  "forbidden": ["actions the agent must not take"],
  "verification": ["commands or checks to run"],
  "output_format": ["how the agent should report or format output"],
  "files": ["explicit file paths or filenames"],
  "warnings": ["risks that should be surfaced"]
}

Raw input:
{raw_text}
"""


def convert_llm_based(raw_text: str, model_name: str) -> dict[str, list[str]]:
    """High-quality semantic compression using a local Ollama model."""
    if ollama is None:
        result = empty_context()
        result["warnings"].append("Ollama Python package is not installed.")
        return result

    prompt = PROMPT_TEMPLATE.replace("{raw_text}", raw_text)

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0},
            format="json",
        )
        result_text = response["message"]["content"]
        return normalize_context(json.loads(result_text))
    except Exception as exc:
        result = empty_context()
        result["warnings"].append(f"LLM conversion failed: {exc}")
        return result
