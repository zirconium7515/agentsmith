import os

SKILLS_DIR_NAME = ".agents/skills"

def setup_skills(project_root: str):
    """Creates default skill templates in the project directory."""
    skills_path = os.path.join(project_root, SKILLS_DIR_NAME)
    
    skills = {
        "code-review": """---
name: code-review
description: Review code changes for correctness, edge cases, style, and project safety.
---
# Code Review Skill
## Steps
1. Inspect changed files.
2. Check correctness.
3. Check edge cases.
4. Check project rules from AGENTS.md.
5. Check dependency changes.
6. Check whether verification commands were run.
## Output Format
- Critical issues
- Minor issues
- Suggested fixes
- Test status""",
        "safe-refactor": """---
name: safe-refactor
description: Safely refactor code without changing behavior.
---
# Safe Refactor Skill
## Rules
- Preserve behavior.
- Do not change public function names unless required.
- Do not change file paths, output names, or data formats.
- Make small, reversible changes.
- Run tests or startup checks after each major change.
## Required Output
- What was refactored
- Why behavior should be unchanged
- Files changed
- Verification result""",
        "git-backup": """---
name: git-backup
description: Prepare safe Git backup workflow for Google Drive source and GitHub backup/deployment projects.
---
# Git Backup Skill
## Workflow
1. Check current branch.
2. Check working tree status.
3. Review changed files.
4. Do not force push.
5. Do not rewrite history.
6. Prepare a short commit message only if requested.
## Safety
- Never commit raw data unless explicitly requested.
- Never delete untracked files automatically.
- Warn if large files, raw data, or binary outputs are staged."""
    }

    for skill_name, content in skills.items():
        skill_dir = os.path.join(skills_path, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        skill_file = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_file):
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(content)
