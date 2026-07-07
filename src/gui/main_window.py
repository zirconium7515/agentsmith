import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import urllib.request
import subprocess
import sys

from src.core.file_manager import read_file, write_file, generate_project_tree
from src.core.safety_checker import get_warnings_for_inclusion
from src.converter.rule_based import convert_rule_based
from src.converter.llm_based import convert_llm_based
from src.converter.model_selector import select_best_model
from src.generators.bundler import render_template, build_context_for_ai
from src.generators.skill_manager import setup_skills

# Use absolute path for VERSION.txt to work with PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VERSION_FILE = os.path.join(BASE_DIR, "VERSION.txt")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/zirconium7515/agentsmith/main/VERSION.txt"

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x650")
        self.root.title("Context Compiler")
        
        self.running = False
        self.current_version = self.load_local_version()
        self.setup_ui()
        
        # Check for updates in background
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        
    def load_local_version(self):
        try:
            with open(VERSION_FILE, 'r') as f:
                return f.read().strip()
        except Exception:
            return "unknown"
            
    def check_for_updates(self):
        try:
            req = urllib.request.Request(REMOTE_VERSION_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                remote_version = response.read().decode('utf-8').strip()
                
            if remote_version and self.current_version != "unknown" and remote_version != self.current_version:
                # Show update button
                self.root.after(0, self.show_update_button, remote_version)
        except Exception as e:
            print(f"Update check failed: {e}")
            
    def show_update_button(self, new_version):
        self.update_btn = ttk.Button(self.header_frame, text=f"✨ Update Available (v{new_version})", command=self.trigger_update)
        self.update_btn.pack(side=tk.RIGHT, padx=10)
        
    def trigger_update(self):
        if messagebox.askyesno("Update", "The app will close and update itself. Continue?"):
            update_script = os.path.join(BASE_DIR, "update_and_build.bat")
            if os.path.exists(update_script):
                subprocess.Popen(f'start cmd /c "{update_script}"', shell=True)
                self.root.quit()
            else:
                messagebox.showerror("Error", "Update script not found!")

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Header (Title + Update Button) ---
        self.header_frame = ttk.Frame(main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(self.header_frame, text=f"Context Compiler v{self.current_version}", font=("Helvetica", 14, "bold")).pack(side=tk.LEFT)
        
        # --- File Selection ---
        file_frame = ttk.LabelFrame(main_frame, text="Paths", padding="5")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Project Folder:").grid(row=0, column=0, sticky=tk.W)
        self.proj_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.proj_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_proj).grid(row=0, column=2)
        
        ttk.Label(file_frame, text="Raw Context File:").grid(row=1, column=0, sticky=tk.W)
        self.raw_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.raw_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_raw).grid(row=1, column=2)
        
        # --- Options ---
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        opt_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(opt_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="Rule-based")
        ttk.Radiobutton(opt_frame, text="Rule-based (Fast)", variable=self.mode_var, value="Rule-based").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="Local LLM (High Quality)", variable=self.mode_var, value="LLM").grid(row=0, column=2, sticky=tk.W)
        
        self.chk_agents = tk.BooleanVar(value=True)
        self.chk_task = tk.BooleanVar(value=True)
        self.chk_compact = tk.BooleanVar(value=True)
        self.chk_bundle = tk.BooleanVar(value=True)
        self.chk_skills = tk.BooleanVar(value=True)
        self.chk_tree = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(opt_frame, text="AGENTS.md", variable=self.chk_agents).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="TASK.md", variable=self.chk_task).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="CONTEXT.compact.md", variable=self.chk_compact).grid(row=1, column=2, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="CONTEXT_FOR_AI.md", variable=self.chk_bundle).grid(row=2, column=0, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Skills", variable=self.chk_skills).grid(row=2, column=1, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="Project Tree", variable=self.chk_tree).grid(row=2, column=2, sticky=tk.W)
        
        # --- Controls ---
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.btn_start = ttk.Button(ctrl_frame, text="Start", command=self.start_process)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = ttk.Button(ctrl_frame, text="Stop", command=self.stop_process, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(ctrl_frame, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # --- Logs & Preview ---
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)
        
        log_frame = ttk.LabelFrame(paned, text="Status Log")
        self.txt_log = tk.Text(log_frame, height=10, width=40)
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        paned.add(log_frame, weight=1)
        
        preview_frame = ttk.LabelFrame(paned, text="Preview (CONTEXT_FOR_AI.md)")
        self.txt_preview = tk.Text(preview_frame, height=10, width=40)
        self.txt_preview.pack(fill=tk.BOTH, expand=True)
        paned.add(preview_frame, weight=2)
        
    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.root.update_idletasks()
        
    def browse_proj(self):
        folder = filedialog.askdirectory()
        if folder:
            self.proj_var.set(folder)
            
    def browse_raw(self):
        file = filedialog.askopenfilename(filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")])
        if file:
            self.raw_var.set(file)
            
    def start_process(self):
        if not self.proj_var.get() or not self.raw_var.get():
            messagebox.showerror("Error", "Please select both project folder and raw context file.")
            return
            
        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.txt_log.delete(1.0, tk.END)
        self.txt_preview.delete(1.0, tk.END)
        
        threading.Thread(target=self.run_pipeline, daemon=True).start()
        
    def stop_process(self):
        self.running = False
        self.log("Stopping process...")
        
    def run_pipeline(self):
        try:
            proj_dir = self.proj_var.get()
            raw_file = self.raw_var.get()
            
            self.log("Reading raw context...")
            raw_text = read_file(raw_file)
            if not raw_text:
                self.log("Failed to read raw file.")
                return
            self.progress['value'] = 10
            
            # 1. Conversion
            self.log(f"Converting using {self.mode_var.get()} mode...")
            if self.mode_var.get() == "LLM":
                self.log("Detecting suitable model...")
                model = select_best_model()
                if "ollama_" in model:
                    self.log(f"LLM Error: {model}. Falling back to Rule-based.")
                    context_data = convert_rule_based(raw_text)
                elif "recommend:" in model:
                    rec = model.split(":")[1]
                    self.log(f"Model {rec} recommended but not installed. Falling back to Rule-based.")
                    context_data = convert_rule_based(raw_text)
                else:
                    self.log(f"Using model: {model}")
                    context_data = convert_llm_based(raw_text, model)
            else:
                context_data = convert_rule_based(raw_text)
                
            if not self.running: return
            self.progress['value'] = 40
            
            # 2. Generation
            self.log("Generating templates...")
            agents_md = ""
            task_md = ""
            compact_md = ""
            tree_str = ""
            
            if self.chk_agents.get():
                agents_md = render_template('agents.md.jinja2', {})
                write_file(os.path.join(proj_dir, "AGENTS.md"), agents_md)
                self.log("Created AGENTS.md")
                
            if self.chk_task.get():
                task_md = render_template('task.md.jinja2', {})
                write_file(os.path.join(proj_dir, "TASK.md"), task_md)
                self.log("Created TASK.md")
                
            if self.chk_compact.get():
                compact_md = render_template('context_compact.md.jinja2', context_data)
                write_file(os.path.join(proj_dir, "CONTEXT.compact.md"), compact_md)
                self.log("Created CONTEXT.compact.md")
                
            if self.chk_tree.get():
                self.log("Generating project tree...")
                tree_str = generate_project_tree(proj_dir)
                
            if not self.running: return
            self.progress['value'] = 70
            
            if self.chk_skills.get():
                self.log("Setting up skills...")
                setup_skills(proj_dir)
                
            if self.chk_bundle.get():
                self.log("Building CONTEXT_FOR_AI.md...")
                bundle = build_context_for_ai(agents_md, compact_md, task_md, tree_str)
                write_file(os.path.join(proj_dir, "CONTEXT_FOR_AI.md"), bundle)
                self.log("Created CONTEXT_FOR_AI.md")
                
                # Show in preview
                self.txt_preview.insert(tk.END, bundle)
                
            self.progress['value'] = 100
            self.log("Finished successfully!")
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.running = False
