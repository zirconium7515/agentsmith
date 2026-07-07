import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import threading
import sys

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AgentSmith Installer")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
        
    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10))
        
        ttk.Label(self.root, text="AgentSmith Setup", font=("Helvetica", 16, "bold")).pack(pady=20)
        
        ttk.Label(self.root, text="설치할 경로를 지정해 주세요:").pack(pady=5)
        
        frame = ttk.Frame(self.root)
        frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.path_var = tk.StringVar(value="C:\\AgentSmith")
        self.entry = ttk.Entry(frame, textvariable=self.path_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(frame, text="찾아보기...", command=self.browse).pack(side=tk.RIGHT)
        
        self.status_var = tk.StringVar(value="설치 준비 완료.")
        self.lbl_status = ttk.Label(self.root, textvariable=self.status_var, foreground="gray")
        self.lbl_status.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=5)
        
        self.btn_install = ttk.Button(self.root, text="설치 시작", command=self.start_install)
        self.btn_install.pack(pady=10)
        
    def browse(self):
        folder = filedialog.askdirectory(title="Select Installation Folder")
        if folder:
            self.path_var.set(os.path.join(folder, "AgentSmith").replace("/", "\\"))
            
    def start_install(self):
        self.btn_install.config(state=tk.DISABLED)
        self.progress.start(10)
        threading.Thread(target=self.run_install, daemon=True).start()
        
    def log(self, msg):
        self.root.after(0, self.status_var.set, msg)
        
    def run_command(self, cmd, shell=False):
        try:
            # CREATE_NO_WINDOW = 0x08000000 to hide console window for subprocesses
            result = subprocess.run(cmd, shell=shell, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=0x08000000)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except FileNotFoundError:
            return False, "Not found"

    def run_install(self):
        install_dir = self.path_var.get()
        if not os.path.exists(install_dir):
            try:
                os.makedirs(install_dir)
            except Exception as e:
                self.log(f"디렉토리 생성 실패: {e}")
                self.root.after(0, self.finish_install, False)
                return
                
        self.log("Git 설치 여부 확인 중...")
        has_git, _ = self.run_command(["git", "--version"])
        if not has_git:
            self.log("Git 무인 설치 중 (시간이 소요될 수 있습니다)...")
            success, _ = self.run_command(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget", "--accept-source-agreements", "--accept-package-agreements", "--silent"])
            if not success:
                self.root.after(0, lambda: messagebox.showerror("설치 오류", "Git 설치에 실패했습니다. 수동으로 설치해주세요."))
                self.root.after(0, self.finish_install, False)
                return
                
        self.log("Python 설치 여부 확인 중...")
        has_python, _ = self.run_command(["python", "--version"])
        if not has_python:
            self.log("Python 무인 설치 중 (시간이 소요될 수 있습니다)...")
            success, _ = self.run_command(["winget", "install", "--id", "Python.Python.3.12", "-e", "--source", "winget", "--accept-source-agreements", "--accept-package-agreements", "--silent"])
            if not success:
                self.root.after(0, lambda: messagebox.showerror("설치 오류", "Python 설치에 실패했습니다. 수동으로 설치해주세요."))
                self.root.after(0, self.finish_install, False)
                return
                
        self.log("최신 소스코드 다운로드 중 (Git Clone)...")
        os.chdir(install_dir)
        if not os.path.exists(".git"):
            # Clone into the current directory ('.') to prevent double nesting (AgentSmith/agentsmith)
            success, err = self.run_command(["git", "clone", "https://github.com/zirconium7515/agentsmith.git", "."])
            if not success:
                self.root.after(0, lambda e=err: messagebox.showerror("설치 오류", f"소스코드 다운로드에 실패했습니다:\n{e}"))
                self.root.after(0, self.finish_install, False)
                return
                
        self.log("빌드 스크립트 실행 준비 중...")
        # (이미 최상위 폴더이므로 더 이상 cd agentsmith 를 하지 않음)
        
        if os.path.exists("update_and_build.bat"):
            # Execute batch file detached (open in a new visible console)
            subprocess.Popen('start update_and_build.bat', shell=True)
            self.root.after(0, self.finish_install, True)
        else:
            self.root.after(0, lambda: messagebox.showerror("설치 오류", "빌드 스크립트를 찾을 수 없습니다!"))
            self.root.after(0, self.finish_install, False)
            
    def finish_install(self, success):
        self.progress.stop()
        if success:
            self.status_var.set("초기 셋업 완료!")
            messagebox.showinfo("설치 완료", "AgentSmith 파일 다운로드가 성공적으로 완료되었습니다!\n이제 터미널 창에서 초기 빌드가 자동으로 진행됩니다.")
            self.root.quit()
        else:
            self.btn_install.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
