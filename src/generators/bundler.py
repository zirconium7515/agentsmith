from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def render_template(template_name: str, data: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(template_name)
    return template.render(**data)

def build_context_for_ai(agents_md: str, context_compact_md: str, task_md: str, project_tree: str, additional_summaries: str = "") -> str:
    """Assembles the final CONTEXT_FOR_AI.md bundle."""
    bundle = [
        "Read this document carefully. Follow AGENTS.md strictly. Complete TASK.md only.",
        "Use the existing Google Drive -> GitHub -> git pull workflow.",
        "Do not suggest clone or worktree alternatives.",
        "\n========================================\n",
        "# 1. AGENTS.md\n",
        agents_md,
        "\n========================================\n",
        "# 2. CONTEXT.compact.md\n",
        context_compact_md,
        "\n========================================\n",
        "# 3. TASK.md\n",
        task_md,
        "\n========================================\n",
        "# 4. Project Tree\n",
        "```\n" + project_tree + "\n```\n"
    ]
    
    if additional_summaries:
        bundle.append("\n========================================\n")
        bundle.append("# 5. Additional Summaries\n")
        bundle.append(additional_summaries)
        
    return "\n".join(bundle)
