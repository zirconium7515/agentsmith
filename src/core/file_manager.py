import os
from pathlib import Path
from typing import List, Optional

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    "data", "raw", "backup", "archive", "dist", "build", ".cache"
}

# results/raw is a bit tricky as a simple set, we'll handle it via path checking
EXCLUDED_PATHS = [
    os.path.normpath("results/raw")
]

def is_excluded(dir_path: str, base_path: str) -> bool:
    rel_path = os.path.relpath(dir_path, base_path)
    if rel_path == ".":
        return False
        
    parts = Path(rel_path).parts
    
    # Check if any part of the path is in excluded dirs
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
        
    # Check specific excluded subpaths
    for excl in EXCLUDED_PATHS:
        if rel_path.startswith(excl) or excl in rel_path:
            return True
            
    return False

def read_file(filepath: str) -> Optional[str]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def write_file(filepath: str, content: str) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False

def generate_project_tree(root_dir: str) -> str:
    """Generates a text-based tree of the project directory."""
    tree_lines = []
    
    def walk_dir(current_dir: str, prefix: str = ""):
        try:
            items = sorted(os.listdir(current_dir))
        except PermissionError:
            return
            
        # Filter items
        filtered_items = []
        for item in items:
            full_path = os.path.join(current_dir, item)
            if not is_excluded(full_path, root_dir):
                filtered_items.append(item)
                
        for i, item in enumerate(filtered_items):
            full_path = os.path.join(current_dir, item)
            is_last = (i == len(filtered_items) - 1)
            
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{item}")
            
            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                walk_dir(full_path, prefix + extension)

    tree_lines.append(os.path.basename(root_dir) + "/")
    walk_dir(root_dir)
    
    return "\n".join(tree_lines)
