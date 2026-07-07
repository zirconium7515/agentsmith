# AgentSmith

AgentSmith is a local GUI context compiler for coding agents.

It converts rough Korean project notes, initial project conditions, and task requests into token-efficient agent-facing files and copy-ready prompts.

## Core Use Cases

- Create project startup context for coding agents.
- Convert Korean natural-language task requests into structured prompts.
- Generate Codex-oriented context files.
- Generate Google Antigravity-oriented planning artifacts.
- Keep project workflow, forbidden actions, verification commands, and output format explicit.

## Target Agents

AgentSmith supports target-specific rendering.

### Codex

Typical outputs:

- `AGENTS.md`
- `TASK.md`
- `CONTEXT.compact.md`
- `CONTEXT_FOR_AI.md`
- optional `.agents/skills/*/SKILL.md`

### Google Antigravity

Typical outputs:

- `.agents/AGENTS.md`
- `implementation_plan.md`
- `task.md`
- `walkthrough.md`
- `CONTEXT.compact.md`
- `CONTEXT_FOR_ANTIGRAVITY.md`

Antigravity output is designed around planning artifacts, task state, final walkthroughs, and rich Markdown review documents.

## Compiler Modes

- **Project Init**: Generate startup rules and compact project context.
- **Task Prompt**: Convert a Korean task request into a copy-ready coding-agent prompt.
- **Full Bundle**: Generate rules, task/planning files, compact context, and final bundle.

## Conversion Engines

- **Rule-based**: Fast, offline, deterministic cleanup and classification.
- **Local LLM**: Uses Ollama for higher-quality semantic compression and JSON schema output.

## Installation For Development

```bash
pip install -r requirements.txt
python main.py
```

## Distribution Model

The intended user flow is:

1. Download `AgentSmith_Installer.exe`.
2. Choose an installation folder.
3. The installer prepares Git/Python if needed, clones this repository, installs dependencies, builds the GUI exe, and launches AgentSmith.
4. On startup, AgentSmith checks GitHub `VERSION.txt`.
5. If a newer version exists, an update button appears.
6. The user can keep using the app or trigger update and rebuild.
7. To uninstall, run `uninstall.bat` from the installation folder.

## Versioning

AgentSmith follows Semantic Versioning.

- Patch: fixes and small maintenance changes.
- Minor: backward-compatible feature additions.
- Major: breaking workflow or file format changes.
