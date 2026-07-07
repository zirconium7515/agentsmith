# Context Compiler

Context Compiler is a local GUI tool that converts rough, unstructured project notes (e.g., long Korean explanations) into token-efficient, strictly formatted Markdown files optimized for AI coding agents like Codex, Antigravity, and Claude.

By passing your project context through this compiler, you provide AI agents with a much cleaner, deterministic environment, preventing hallucinations and workflow deviations.

## Features

- **Token Optimization**: Strips emotional/filler text and converts sentences into concise technical bullet points.
- **Dual Engine**: 
  - **Rule-based (Fast)**: Offline, regex-based keyword classification and deduplication.
  - **Local LLM (High Quality)**: Integrates with local `Ollama` to enforce strict JSON schemas and high-quality semantic compression.
- **Safety First**: Automatically detects large files, raw data directories, and Google Drive sync conflicts.
- **Skill Generation**: Automatically scaffolds `.agents/skills/` directories with standard reusable workflows (Code Review, Safe Refactor, Git Backup).

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/context-compiler.git
cd context-compiler

# Install dependencies
pip install -r requirements.txt
```

## Usage

Ensure you have [Ollama](https://ollama.ai/) installed and running if you intend to use the Local LLM mode.

```bash
python main.py
```

1. Select your target project folder.
2. Select your raw context file (e.g., `CONTEXT.raw.ko.md`).
3. Choose the conversion mode (Rule-based or LLM).
4. Click **Start**.

The compiler will generate standard agent files (`AGENTS.md`, `TASK.md`, `CONTEXT.compact.md`, and a final `CONTEXT_FOR_AI.md` bundle) directly into your selected project folder.
