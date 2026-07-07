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
- Return JSON only.

Required schema:
{
  "project": ["short project identity bullets"],
  "goal": ["what the user wants to achieve"],
  "context": ["important background"],
  "environment": ["OS, runtime, dependencies, tools"],
  "workflow": ["development, deployment, update, or collaboration workflow"],
  "rules": ["stable coding or project rules"],
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
