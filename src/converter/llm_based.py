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

Translation and Rewriting Rules:
- Translate Korean natural language sentences into short, technical English bullets.
- Examples of translation:
  * "개발한 코드는 깃헙에 push 한다." -> "Push developed code to GitHub."
  * "X는 대규모 패치이다." -> "Increment X for large-scale patches."
  * "venv등의 무거운 실행 프로그램들은 구글 드라이브 상에서 구동하기 힘드므로 gitignore에 넣는다." -> "Add virtual environments such as venv/ to .gitignore."
  * "깃헙에 push는 다음의 버전룰에 맞춰서 push한다." -> "Push developed code to GitHub according to versioning rules."
  * "Y는 X버전 상에서 주요 기능의 추가 및 개편이 있는 패치이다." -> "Increment Y for major feature additions or redesigns within the same X version."
  * "Z는 Y버전 상에서 소규모 기능의 패치 혹은 버그 패치 등 자잘한 패치이다." -> "Increment Z for small feature patches, bug fixes, or minor maintenance patches within the same Y version."
  * "git push를 할 경우 commit 메세지에 버전을 표기한다." -> "Include the version in the commit message when pushing to GitHub."
  * "로컬에서 구동할 경우 git pull을 통해 업데이트를 받는다." -> "Runtime machines update through git pull."
  * "따라서 개발은 반드시 구글드라이브 상에서만 한다." -> "Active development must happen in the Google Drive workspace."

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
