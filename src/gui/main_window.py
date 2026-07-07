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

ENGINE_LABELS = {
    "Rule-based": "규칙 기반",
    "LLM": "로컬 LLM",
}


def parse_version(version: str) -> tuple[int, int, int]:
    parts = version.strip().lstrip("v").split(".")
    numbers = []
    for part in parts[:3]:
        try:
            numbers.append(int(part))
        except ValueError:
            numbers.append(0)
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers)


def is_remote_newer(local_version: str, remote_version: str) -> bool:
    if local_version == "unknown" or not remote_version:
        return False
    return parse_version(remote_version) > parse_version(local_version)

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
        self.root.geometry("1150x850")
        self.root.title(APP_NAME)

        self.running = False
        self.current_version = self.load_local_version()
        self.preview_text = ""
        self.setup_ui()

        threading.Thread(target=self.check_for_updates, args=(False,), daemon=True).start()

    def load_local_version(self) -> str:
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as file:
                return file.read().strip()
        except Exception:
            return "unknown"

    def check_for_updates(self, manual: bool = False) -> None:
        try:
            req = urllib.request.Request(REMOTE_VERSION_URL, headers={"User-Agent": APP_NAME})
            with urllib.request.urlopen(req, timeout=5) as response:
                remote_version = response.read().decode("utf-8").strip()

            if is_remote_newer(self.current_version, remote_version):
                self.root.after(0, lambda: self.handle_update_found(remote_version, manual))
            else:
                self.root.after(0, lambda: self.handle_no_update_found(manual))
        except Exception as exc:
            self.root.after(0, lambda: self.handle_update_error(exc, manual))

    def manual_check_update(self) -> None:
        self.btn_check_update.config(state=tk.DISABLED)
        self.log("업데이트 확인 중...")
        threading.Thread(target=self.check_for_updates, args=(True,), daemon=True).start()

    def handle_update_found(self, new_version: str, manual: bool) -> None:
        self.btn_check_update.config(state=tk.NORMAL, text=f"업데이트 설치: v{new_version}", command=self.trigger_update)
        self.log(f"새로운 업데이트 버전을 발견했습니다: v{new_version}")
        if manual:
            if messagebox.askyesno("업데이트 발견", f"새로운 버전 v{new_version}이 존재합니다.\n지금 업데이트하시겠습니까?"):
                self.trigger_update()

    def handle_no_update_found(self, manual: bool) -> None:
        self.btn_check_update.config(state=tk.NORMAL)
        self.log("이미 최신 버전을 사용 중입니다.")
        if manual:
            messagebox.showinfo("업데이트 확인", f"현재 최신 버전을 사용 중입니다.\n(설치된 버전: v{self.current_version})")

    def handle_update_error(self, exc: Exception, manual: bool) -> None:
        self.btn_check_update.config(state=tk.NORMAL)
        self.log(f"업데이트 확인 실패: {exc}")
        if manual:
            messagebox.showerror("업데이트 확인 실패", f"업데이트 정보를 확인하는 데 실패했습니다:\n{exc}")

    def trigger_update(self) -> None:
        if not messagebox.askyesno("업데이트", "AgentSmith를 종료하고 지금 업데이트할까요?"):
            return

        update_script = os.path.join(BASE_DIR, "update_and_build.bat")
        if os.path.exists(update_script):
            subprocess.Popen(f'start cmd /c "{update_script}"', shell=True)
            self.root.quit()
        else:
            messagebox.showerror("오류", "업데이트 스크립트를 찾을 수 없습니다.")

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

        self.btn_check_update = ttk.Button(
            self.header_frame,
            text="업데이트 확인",
            command=self.manual_check_update
        )
        self.btn_check_update.pack(side=tk.RIGHT, padx=10)

        path_frame = ttk.LabelFrame(main_frame, text="프로젝트 및 입력", padding="8")
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="프로젝트 폴더:").grid(row=0, column=0, sticky=tk.W)
        self.proj_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.proj_var, width=80).grid(row=0, column=1, padx=5, sticky=tk.EW)
        ttk.Button(path_frame, text="찾아보기...", command=self.browse_proj).grid(row=0, column=2)

        ttk.Label(path_frame, text="원본 문맥 파일:").grid(row=1, column=0, sticky=tk.W)
        self.raw_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.raw_var, width=80).grid(row=1, column=1, padx=5, sticky=tk.EW)
        ttk.Button(path_frame, text="찾아보기...", command=self.browse_raw).grid(row=1, column=2)
        path_frame.columnconfigure(1, weight=1)

        input_frame = ttk.LabelFrame(main_frame, text="한국어 문맥 또는 작업 요청 직접 입력", padding="8")
        input_frame.pack(fill=tk.BOTH, pady=5)
        self.txt_input = tk.Text(input_frame, height=7, wrap=tk.WORD)
        self.txt_input.pack(fill=tk.BOTH, expand=True)

        opt_frame = ttk.LabelFrame(main_frame, text="컴파일 옵션", padding="8")
        opt_frame.pack(fill=tk.X, pady=5)

        ttk.Label(opt_frame, text="대상 에이전트:").grid(row=0, column=0, sticky=tk.W)
        self.agent_var = tk.StringVar(value="Codex")
        ttk.Radiobutton(opt_frame, text="코덱스 (Codex)", variable=self.agent_var, value="Codex").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="안티그래비티 (Antigravity)", variable=self.agent_var, value="Antigravity").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(opt_frame, text="작업 흐름:").grid(row=1, column=0, sticky=tk.W)
        self.workflow_var = tk.StringVar(value="Project Init")
        ttk.Radiobutton(opt_frame, text="프로젝트 초기 조건", variable=self.workflow_var, value="Project Init").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="작업 프롬프트", variable=self.workflow_var, value="Task Prompt").grid(row=1, column=2, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="전체 번들", variable=self.workflow_var, value="Full Bundle").grid(row=1, column=3, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="프롬프트만", variable=self.workflow_var, value="Prompt Only").grid(row=1, column=4, sticky=tk.W)

        ttk.Label(opt_frame, text="변환 엔진:").grid(row=2, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="Rule-based")
        ttk.Radiobutton(opt_frame, text="규칙 기반", variable=self.mode_var, value="Rule-based").grid(row=2, column=1, sticky=tk.W)
        ttk.Radiobutton(opt_frame, text="로컬 LLM", variable=self.mode_var, value="LLM").grid(row=2, column=2, sticky=tk.W)

        self.chk_agents = tk.BooleanVar(value=True)
        self.chk_task = tk.BooleanVar(value=False)
        self.chk_compact = tk.BooleanVar(value=True)
        self.chk_bundle = tk.BooleanVar(value=True)
        self.chk_skills = tk.BooleanVar(value=False)
        self.chk_tree = tk.BooleanVar(value=True)

        self.workflow_var.trace_add("write", self.on_workflow_change)

        self.btn_chk_agents = ttk.Checkbutton(opt_frame, text="규칙 파일", variable=self.chk_agents)
        self.btn_chk_agents.grid(row=3, column=0, sticky=tk.W)
        self.btn_chk_task = ttk.Checkbutton(opt_frame, text="작업/계획 파일", variable=self.chk_task)
        self.btn_chk_task.grid(row=3, column=1, sticky=tk.W)
        self.btn_chk_compact = ttk.Checkbutton(opt_frame, text="압축 문맥", variable=self.chk_compact)
        self.btn_chk_compact.grid(row=3, column=2, sticky=tk.W)
        self.btn_chk_bundle = ttk.Checkbutton(opt_frame, text="최종 번들", variable=self.chk_bundle)
        self.btn_chk_bundle.grid(row=3, column=3, sticky=tk.W)
        self.btn_chk_skills = ttk.Checkbutton(opt_frame, text="스킬", variable=self.chk_skills)
        self.btn_chk_skills.grid(row=4, column=1, sticky=tk.W)
        self.btn_chk_tree = ttk.Checkbutton(opt_frame, text="프로젝트 트리", variable=self.chk_tree)
        self.btn_chk_tree.grid(row=4, column=2, sticky=tk.W)

        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=5)

        self.btn_start = ttk.Button(ctrl_frame, text="컴파일", command=self.start_process)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(ctrl_frame, text="중지", command=self.stop_process, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_copy = ttk.Button(ctrl_frame, text="미리보기 복사", command=self.copy_preview)
        self.btn_copy.pack(side=tk.LEFT, padx=5)

        self.lbl_tokens = ttk.Label(ctrl_frame, text="예상 토큰 수: 0")
        self.lbl_tokens.pack(side=tk.RIGHT, padx=5)

        self.progress = ttk.Progressbar(ctrl_frame, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        log_frame = ttk.LabelFrame(paned, text="상태 로그")
        self.txt_log = tk.Text(log_frame, height=10, width=42, wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        paned.add(log_frame, weight=1)

        preview_frame = ttk.LabelFrame(paned, text="미리보기")
        self.txt_preview = tk.Text(preview_frame, height=10, width=72, wrap=tk.WORD)
        self.txt_preview.pack(fill=tk.BOTH, expand=True)
        paned.add(preview_frame, weight=2)

        self.on_workflow_change()

    def browse_proj(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.proj_var.set(folder)

    def browse_raw(self) -> None:
        file = filedialog.askopenfilename(
            filetypes=[
                ("마크다운 파일", "*.md"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*"),
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
        self.log("미리보기를 클립보드에 복사했습니다.")

    def start_process(self) -> None:
        direct_text = self.txt_input.get("1.0", tk.END).strip()
        if not self.raw_var.get() and not direct_text:
            messagebox.showerror("오류", "원본 문맥 파일을 선택하거나 직접 문맥을 입력하세요.")
            return

        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.preview_text = ""
        self.txt_log.delete(1.0, tk.END)
        self.txt_preview.delete(1.0, tk.END)
        self.lbl_tokens.config(text="예상 토큰 수: 0")

        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def stop_process(self) -> None:
        self.running = False
        self.log("작업을 중지하는 중...")

    def collect_input(self) -> tuple[str, list[str]]:
        input_parts: list[str] = []
        warnings: list[str] = []

        raw_file = self.raw_var.get().strip()
        if raw_file:
            self.log("원본 문맥 파일을 읽는 중...")
            warnings.extend(get_warnings_for_inclusion(raw_file))
            raw_text = read_file(raw_file)
            if raw_text:
                input_parts.append(raw_text)
            else:
                warnings.append(f"원본 문맥 파일을 읽지 못했습니다: {raw_file}")

        direct_text = self.txt_input.get("1.0", tk.END).strip()
        if direct_text:
            input_parts.append(direct_text)

        return "\n\n".join(input_parts), warnings

    def convert_context(self, raw_text: str) -> dict[str, list[str]]:
        engine_label = ENGINE_LABELS.get(self.mode_var.get(), self.mode_var.get())
        self.log(f"{engine_label} 엔진으로 변환하는 중...")
        if self.mode_var.get() != "LLM":
            return convert_rule_based(raw_text)

        self.log("로컬 Ollama 모델을 확인하는 중...")
        model = select_best_model()
        if model.startswith("ollama_"):
            self.log(f"로컬 LLM을 사용할 수 없습니다: {model}. 규칙 기반으로 전환합니다.")
            return convert_rule_based(raw_text)
        if model.startswith("recommend:"):
            self.log(f"추천 모델이 설치되어 있지 않습니다: {model.split(':', 1)[1]}. 규칙 기반으로 전환합니다.")
            return convert_rule_based(raw_text)

        self.log(f"사용 모델: {model}")
        return convert_llm_based(raw_text, model)

    def run_pipeline(self) -> None:
        try:
            proj_dir = self.proj_var.get().strip()
            if not proj_dir and self.workflow_var.get() != "Prompt Only":
                self.log("[경고] 프로젝트 폴더가 지정되지 않아 파일 저장 및 트리 생성은 생략됩니다.")

            raw_text, warnings = self.collect_input()
            if not raw_text:
                self.log("입력 문맥이 없습니다.")
                return
            self.progress["value"] = 15

            context_data = normalize_context(self.convert_context(raw_text))
            context_data["warnings"].extend(warnings)
            self.progress["value"] = 45

            tree_str = ""
            if proj_dir and self.chk_tree.get():
                self.log("프로젝트 트리를 생성하는 중...")
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

            if proj_dir:
                for relative_path, content in outputs.items():
                    write_file(os.path.join(proj_dir, relative_path), content)
                    self.log(f"생성 완료: {relative_path}")

                if self.chk_skills.get():
                    self.log("스킬 템플릿을 생성하는 중...")
                    setup_skills(proj_dir)
            else:
                self.log("파일 저장 없이 변환이 완료되었습니다.")

            self.preview_text = preview
            self.txt_preview.insert(tk.END, preview)
            self.lbl_tokens.config(text=f"예상 토큰 수: {estimate_tokens(preview)}")
            self.progress["value"] = 100
            self.log("작업이 완료되었습니다.")
        except Exception as exc:
            self.log(f"오류: {exc}")
        finally:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.running = False

    def on_workflow_change(self, *args) -> None:
        mode = self.workflow_var.get()
        if mode == "Prompt Only":
            if not hasattr(self, "_in_prompt_only") or not self._in_prompt_only:
                self._saved_chk_states = {
                    "agents": self.chk_agents.get(),
                    "task": self.chk_task.get(),
                    "compact": self.chk_compact.get(),
                    "bundle": self.chk_bundle.get(),
                    "skills": self.chk_skills.get(),
                    "tree": self.chk_tree.get(),
                }
                self._in_prompt_only = True

            self.chk_agents.set(False)
            self.chk_task.set(False)
            self.chk_compact.set(False)
            self.chk_bundle.set(False)
            self.chk_skills.set(False)
            self.chk_tree.set(False)

            self.btn_chk_agents.config(state=tk.DISABLED)
            self.btn_chk_task.config(state=tk.DISABLED)
            self.btn_chk_compact.config(state=tk.DISABLED)
            self.btn_chk_bundle.config(state=tk.DISABLED)
            self.btn_chk_skills.config(state=tk.DISABLED)
            self.btn_chk_tree.config(state=tk.DISABLED)
        else:
            self.btn_chk_agents.config(state=tk.NORMAL)
            self.btn_chk_task.config(state=tk.NORMAL)
            self.btn_chk_compact.config(state=tk.NORMAL)
            self.btn_chk_bundle.config(state=tk.NORMAL)
            self.btn_chk_skills.config(state=tk.NORMAL)
            self.btn_chk_tree.config(state=tk.NORMAL)

            if hasattr(self, "_in_prompt_only") and self._in_prompt_only:
                self._in_prompt_only = False
                if hasattr(self, "_saved_chk_states"):
                    self.chk_agents.set(self._saved_chk_states["agents"])
                    self.chk_task.set(self._saved_chk_states["task"])
                    self.chk_compact.set(self._saved_chk_states["compact"])
                    self.chk_bundle.set(self._saved_chk_states["bundle"])
                    self.chk_skills.set(self._saved_chk_states["skills"])
                    self.chk_tree.set(self._saved_chk_states["tree"])

            # Apply normal modes check logic
            if mode == "Project Init":
                self.chk_task.set(False)
            else:
                self.chk_task.set(True)
