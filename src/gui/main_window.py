from __future__ import annotations

import os
import subprocess
import sys
import threading
import urllib.request
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from src.converter.llm_based import convert_llm_based
from src.converter.model_selector import select_best_model
from src.converter.rule_based import convert_rule_based
from src.converter.schema import estimate_tokens, normalize_context
from src.core.file_manager import generate_project_tree, read_file, write_file
from src.core.safety_checker import get_warnings_for_inclusion
from src.generators.renderers import build_agent_outputs
from src.generators.skill_manager import setup_skills


APP_NAME = "AgentSmith"

def get_base_dir() -> str:
    if not getattr(sys, "frozen", False):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    exe_dir = os.path.dirname(sys.executable)
    install_root = os.path.abspath(os.path.join(exe_dir, os.pardir, os.pardir))
    if os.path.exists(os.path.join(install_root, "VERSION.txt")):
        return install_root
    return exe_dir


BASE_DIR = get_base_dir()

VERSION_FILE = os.path.join(BASE_DIR, "VERSION.txt")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/zirconium7515/agentsmith/master/VERSION.txt"


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("1000x760")
        self.root.title(APP_NAME)

        self.running = False
        self.current_version = self.load_local_version()
        self.preview_text = ""
        self.setup_ui()

        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def load_local_version(self) -> str:
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as file:
                return file.read().strip()
        except Exception:
            return "unknown"

    def check_for_updates(self) -> None:
        try:
            req = urllib.request.Request(REMOTE_VERSION_URL, headers={"User-Agent": APP_NAME})
            with urllib.request.urlopen(req, timeout=5) as response:
                remote_version = response.read().decode("utf-8").strip()

            if remote_version and self.current_version != "unknown" and remote_version != self.current_version:
                self.root.after(0, self.show_update_button, remote_version)
        except Exception as exc:
            print(f"Update check failed: {exc}")

    def show_update_button(self, new_version: str) -> None:
        self.update_btn = ttk.Button(
            self.header_frame,
            text=f"Update available: v{new_version}",
            command=self.trigger_update,
        )
        self.update_btn.pack(side=tk.RIGHT, padx=10)

    def trigger_update(self) -> None:
        if not messagebox.askyesno("Update", "Close AgentSmith and update now?"):
            return

        update_script = os.path.join(BASE_DIR, "update_and_build.bat")
        if os.path.exists(update_script):
            subprocess.Popen(f'start cmd /c "{update_script}"', shell=True)
            self.root.quit()
        else:
            messagebox.showerror("Error", "Update script not found.")

    def setup_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.header_frame = ttk.Frame(main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            self.header_frame,
            text=f"{APP_NAME} v{self.current_version}",
            font=("Helvetica", 14, "bold"),
        ).pack(side=tk.LEFT)

        path_frame = ttk.LabelFrame(main_frame, text="Project and input", padding="8")
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="Project folder:").grid(row=0, column=0, sticky=tk.W)
        self.proj_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.proj_var, width=80).grid(row=0, column=1, padx=5, sticky=tk.EW)
        ttk.Button(path_frame, text="Browse...", command=self.browse_proj).grid(row=0, column=2)

        ttk.Label(path_frame, text="Raw context file:").grid(row=1, column=0, sticky=tk.W)
        self.raw_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.raw_var, width=80).grid(row=1, column=1, padx=5, sticky=tk.EW)
        ttk.Button(path_frame, text="Browse...", command=self.browse_raw).grid(row=1, column=2)
        path_frame.columnconfigure(1, weight=1)

        input_frame = ttk.LabelFrame(main_frame, text="Direct Korean context or task request", padding="8")
        input_frame.pack(fill=tk.BOTH, pady=5)
        self.txt_input = tk.Text(input_frame, height=7, wrap=tk.WORD)
        self.txt_input.pack(fill=tk.BOTH, expand=True)

        opt_frame = ttk.LabelFrame(main_frame, text="Compiler options", padding="8")
        opt_frame.pack(fill=tk.X, pady=5)

        ttk.Label(opt_frame, text="Target agent:").grid(row=0, column=0, sticky=tk.W)
        self.agent_var = tk.StringVar(value="Codex")
        ttk.Radiobutton(opt_frame, text="Codex", variable=self.agent_var, value="Codex").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="Antigravity", variable=self.agent_var, value="Antigravity").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(opt_frame, text="Workflow:").grid(row=1, column=0, sticky=tk.W)
        self.workflow_var = tk.StringVar(value="Project Init")
        ttk.Radiobutton(opt_frame, text="Project Init", variable=self.workflow_var, value="Project Init").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="Task Prompt", variable=self.workflow_var, value="Task Prompt").grid(row=1, column=2, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="Full Bundle", variable=self.workflow_var, value="Full Bundle").grid(row=1, column=3, sticky=tk.W)

        ttk.Label(opt_frame, text="Engine:").grid(row=2, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="Rule-based")
        ttk.Radiobutton(opt_frame, text="Rule-based", variable=self.mode_var, value="Rule-based").grid(row=2, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="Local LLM", variable=self.mode_var, value="LLM").grid(row=2, column=2, sticky=tk.W)

        self.chk_agents = tk.BooleanVar(value=True)
        self.chk_task = tk.BooleanVar(value=True)
        self.chk_compact = tk.BooleanVar(value=True)
        self.chk_bundle = tk.BooleanVar(value=True)
        self.chk_skills = tk.BooleanVar(value=False)
        self.chk_tree = tk.BooleanVar(value=True)

        ttk.Checkbutton(opt_frame, text="Rules file", variable=self.chk_agents).grid(row=3, column=0, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Task/planning files", variable=self.chk_task).grid(row=3, column=1, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Compact context", variable=self.chk_compact).grid(row=3, column=2, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Final bundle", variable=self.chk_bundle).grid(row=3, column=3, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Skills", variable=self.chk_skills).grid(row=4, column=1, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Project tree", variable=self.chk_tree).grid(row=4, column=2, sticky=tk.W)

        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=5)

        self.btn_start = ttk.Button(ctrl_frame, text="Compile", command=self.start_process)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(ctrl_frame, text="Stop", command=self.stop_process, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_copy = ttk.Button(ctrl_frame, text="Copy preview", command=self.copy_preview)
        self.btn_copy.pack(side=tk.LEFT, padx=5)

        self.lbl_tokens = ttk.Label(ctrl_frame, text="Estimated tokens: 0")
        self.lbl_tokens.pack(side=tk.RIGHT, padx=5)

        self.progress = ttk.Progressbar(ctrl_frame, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        log_frame = ttk.LabelFrame(paned, text="Status log")
        self.txt_log = tk.Text(log_frame, height=10, width=42, wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        paned.add(log_frame, weight=1)

        preview_frame = ttk.LabelFrame(paned, text="Preview")
        self.txt_preview = tk.Text(preview_frame, height=10, width=72, wrap=tk.WORD)
        self.txt_preview.pack(fill=tk.BOTH, expand=True)
        paned.add(preview_frame, weight=2)

    def browse_proj(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.proj_var.set(folder)

    def browse_raw(self) -> None:
        file = filedialog.askopenfilename(
            filetypes=[
                ("Markdown files", "*.md"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ]
        )
        if file:
            self.raw_var.set(file)

    def log(self, msg: str) -> None:
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.root.update_idletasks()

    def copy_preview(self) -> None:
        if not self.preview_text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.preview_text)
        self.log("Preview copied to clipboard.")

    def start_process(self) -> None:
        if not self.proj_var.get():
            messagebox.showerror("Error", "Please select a project folder.")
            return

        direct_text = self.txt_input.get("1.0", tk.END).strip()
        if not self.raw_var.get() and not direct_text:
            messagebox.showerror("Error", "Select a raw context file or enter direct context text.")
            return

        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.preview_text = ""
        self.txt_log.delete(1.0, tk.END)
        self.txt_preview.delete(1.0, tk.END)
        self.lbl_tokens.config(text="Estimated tokens: 0")

        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def stop_process(self) -> None:
        self.running = False
        self.log("Stopping process...")

    def collect_input(self) -> tuple[str, list[str]]:
        input_parts: list[str] = []
        warnings: list[str] = []

        raw_file = self.raw_var.get().strip()
        if raw_file:
            self.log("Reading raw context file...")
            warnings.extend(get_warnings_for_inclusion(raw_file))
            raw_text = read_file(raw_file)
            if raw_text:
                input_parts.append(raw_text)
            else:
                warnings.append(f"Could not read raw context file: {raw_file}")

        direct_text = self.txt_input.get("1.0", tk.END).strip()
        if direct_text:
            input_parts.append(direct_text)

        return "\n\n".join(input_parts), warnings

    def convert_context(self, raw_text: str) -> dict[str, list[str]]:
        self.log(f"Converting with {self.mode_var.get()} engine...")
        if self.mode_var.get() != "LLM":
            return convert_rule_based(raw_text)

        self.log("Detecting local Ollama model...")
        model = select_best_model()
        if model.startswith("ollama_"):
            self.log(f"Local LLM unavailable: {model}. Falling back to rule-based.")
            return convert_rule_based(raw_text)
        if model.startswith("recommend:"):
            self.log(f"Recommended model is not installed: {model.split(':', 1)[1]}. Falling back to rule-based.")
            return convert_rule_based(raw_text)

        self.log(f"Using model: {model}")
        return convert_llm_based(raw_text, model)

    def run_pipeline(self) -> None:
        try:
            proj_dir = self.proj_var.get()
            raw_text, warnings = self.collect_input()
            if not raw_text:
                self.log("No input text available.")
                return
            self.progress["value"] = 15

            context_data = normalize_context(self.convert_context(raw_text))
            context_data["warnings"].extend(warnings)
            self.progress["value"] = 45

            tree_str = ""
            if self.chk_tree.get():
                self.log("Generating project tree...")
                tree_str = generate_project_tree(proj_dir)

            if not self.running:
                return
            self.progress["value"] = 65

            outputs, preview = build_agent_outputs(
                context_data=context_data,
                target_agent=self.agent_var.get(),
                workflow_mode=self.workflow_var.get(),
                project_tree=tree_str,
                include_agents=self.chk_agents.get(),
                include_task=self.chk_task.get(),
                include_compact=self.chk_compact.get(),
                include_bundle=self.chk_bundle.get(),
            )

            for relative_path, content in outputs.items():
                write_file(os.path.join(proj_dir, relative_path), content)
                self.log(f"Created {relative_path}")

            if self.chk_skills.get():
                self.log("Setting up skill templates...")
                setup_skills(proj_dir)

            self.preview_text = preview
            self.txt_preview.insert(tk.END, preview)
            self.lbl_tokens.config(text=f"Estimated tokens: {estimate_tokens(preview)}")
            self.progress["value"] = 100
            self.log("Finished successfully.")
        except Exception as exc:
            self.log(f"Error: {exc}")
        finally:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.running = False
