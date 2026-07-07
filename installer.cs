using System;
using System.Windows.Forms;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Drawing;

namespace AgentSmithInstaller
{
    public class InstallerForm : Form
    {
        private Label lblStatus;
        private Button btnInstall;
        private TextBox txtPath;
        private Button btnBrowse;
        private ProgressBar progressBar;
        private TextBox txtLog;

        public InstallerForm()
        {
            this.Text = "AgentSmith Installer";
            this.Size = new Size(500, 400);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;

            Label lblTitle = new Label();
            lblTitle.Text = "AgentSmith Setup";
            lblTitle.Font = new Font("Arial", 14, FontStyle.Bold);
            lblTitle.Location = new Point(160, 15);
            lblTitle.AutoSize = true;
            this.Controls.Add(lblTitle);

            Label lblDesc = new Label();
            lblDesc.Text = "설치할 경로를 지정해 주세요:";
            lblDesc.Location = new Point(20, 50);
            lblDesc.AutoSize = true;
            this.Controls.Add(lblDesc);

            txtPath = new TextBox();
            txtPath.Text = @"C:\AgentSmith";
            txtPath.Location = new Point(20, 70);
            txtPath.Width = 360;
            this.Controls.Add(txtPath);

            btnBrowse = new Button();
            btnBrowse.Text = "찾아보기...";
            btnBrowse.Location = new Point(390, 68);
            btnBrowse.Click += BtnBrowse_Click;
            this.Controls.Add(btnBrowse);

            lblStatus = new Label();
            lblStatus.Text = "설치 준비 완료.";
            lblStatus.ForeColor = Color.Gray;
            lblStatus.Location = new Point(20, 100);
            lblStatus.AutoSize = true;
            this.Controls.Add(lblStatus);

            progressBar = new ProgressBar();
            progressBar.Style = ProgressBarStyle.Marquee;
            progressBar.Location = new Point(20, 120);
            progressBar.Width = 445;
            progressBar.Height = 15;
            progressBar.Visible = false;
            this.Controls.Add(progressBar);

            txtLog = new TextBox();
            txtLog.Multiline = true;
            txtLog.ReadOnly = true;
            txtLog.ScrollBars = ScrollBars.Vertical;
            txtLog.Location = new Point(20, 145);
            txtLog.Width = 445;
            txtLog.Height = 150;
            txtLog.BackColor = Color.Black;
            txtLog.ForeColor = Color.LightGray;
            txtLog.Font = new Font("Consolas", 9);
            this.Controls.Add(txtLog);

            btnInstall = new Button();
            btnInstall.Text = "설치 시작";
            btnInstall.Location = new Point(190, 315);
            btnInstall.Width = 100;
            btnInstall.Height = 35;
            btnInstall.Click += BtnInstall_Click;
            this.Controls.Add(btnInstall);
        }

        private void BtnBrowse_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog())
            {
                fbd.Description = "설치할 최상위 폴더를 선택하세요.";
                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    txtPath.Text = Path.Combine(fbd.SelectedPath, "AgentSmith");
                }
            }
        }

        private void Log(string msg)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string>(Log), new object[] { msg });
                return;
            }
            lblStatus.Text = msg;
            AppendLog(msg);
        }

        private void AppendLog(string text)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string>(AppendLog), new object[] { text });
                return;
            }
            txtLog.AppendText(text + Environment.NewLine);
        }

        private void RefreshPath()
        {
            try {
                string sysPath = Environment.GetEnvironmentVariable("Path", EnvironmentVariableTarget.Machine);
                string usrPath = Environment.GetEnvironmentVariable("Path", EnvironmentVariableTarget.User);
                Environment.SetEnvironmentVariable("Path", sysPath + ";" + usrPath, EnvironmentVariableTarget.Process);
            } catch { }
        }

        private void RunCommandWithOutput(string fileName, string args, string workingDir = null)
        {
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = fileName;
            psi.Arguments = args;
            psi.CreateNoWindow = true;
            psi.UseShellExecute = false;
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardError = true;
            if (workingDir != null)
                psi.WorkingDirectory = workingDir;

            Process p = new Process();
            p.StartInfo = psi;
            p.OutputDataReceived += (s, ev) => { if (ev.Data != null) AppendLog(ev.Data); };
            p.ErrorDataReceived += (s, ev) => { if (ev.Data != null) AppendLog(ev.Data); };
            
            p.Start();
            p.BeginOutputReadLine();
            p.BeginErrorReadLine();
            p.WaitForExit();

            if (p.ExitCode != 0) throw new Exception("명령 실행 실패: " + fileName + " " + args);
        }

        private bool CheckCommand(string cmd)
        {
            try {
                ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c " + cmd + " --version");
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                Process p = Process.Start(psi);
                p.WaitForExit();
                return p.ExitCode == 0;
            } catch { return false; }
        }

        private void BtnInstall_Click(object sender, EventArgs e)
        {
            string installDir = txtPath.Text;
            btnInstall.Enabled = false;
            btnBrowse.Enabled = false;
            txtPath.Enabled = false;
            progressBar.Visible = true;
            txtLog.Clear();

            Thread t = new Thread(() =>
            {
                try
                {
                    if (!Directory.Exists(installDir))
                    {
                        Directory.CreateDirectory(installDir);
                    }

                    Log("[System] Git 설치 여부 확인 중...");
                    if (!CheckCommand("git"))
                    {
                        Log("[System] Git 무인 설치 중 (시간이 소요될 수 있습니다)...");
                        RunCommandWithOutput("winget", "install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements --silent");
                        RefreshPath();
                    }

                    Log("[System] Python 설치 여부 확인 중...");
                    if (!CheckCommand("python"))
                    {
                        Log("[System] Python 무인 설치 중 (시간이 소요될 수 있습니다)...");
                        RunCommandWithOutput("winget", "install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements --silent");
                        RefreshPath();
                    }

                    Log("[System] 최신 소스코드 다운로드 중 (Git Clone)...");
                    if (!Directory.Exists(Path.Combine(installDir, ".git")))
                    {
                        RunCommandWithOutput("git", "clone https://github.com/zirconium7515/agentsmith.git .", installDir);
                    }

                    Log("[System] 백그라운드 빌드 스크립트 실행 중...");
                    string buildScript = Path.Combine(installDir, "update_and_build.bat");
                    if (File.Exists(buildScript))
                    {
                        // --no-start 인자를 전달하여 빌드 후 스크립트 내에서 exe를 실행하지 않도록 합니다 (파이프 블로킹 방지)
                        RunCommandWithOutput("cmd.exe", "/c update_and_build.bat --no-start", installDir);
                    }
                    else
                    {
                        MessageBox.Show("빌드 스크립트를 찾을 수 없습니다!", "오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }

                    this.Invoke(new Action(() => {
                        progressBar.Visible = false;
                        lblStatus.Text = "초기 셋업 및 빌드 완료!";
                        MessageBox.Show("AgentSmith 설치 및 빌드가 완벽하게 마무리되었습니다!\n프로그램이 시작됩니다.", "설치 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        
                        // 직접 exe 실행 (단독 프로세스)
                        string exePath = Path.Combine(installDir, @"dist\AgentSmith\AgentSmith.exe");
                        if (File.Exists(exePath))
                        {
                            ProcessStartInfo psi = new ProcessStartInfo();
                            psi.FileName = exePath;
                            psi.WorkingDirectory = installDir;
                            psi.UseShellExecute = true;
                            Process.Start(psi);
                        }
                        
                        Application.Exit();
                    }));
                }
                catch (Exception ex)
                {
                    this.Invoke(new Action(() => {
                        progressBar.Visible = false;
                        AppendLog("[ERROR] " + ex.Message);
                        MessageBox.Show("설치 중 오류가 발생했습니다. 로그 창을 확인해 주세요.", "오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        btnInstall.Enabled = true;
                        btnBrowse.Enabled = true;
                        txtPath.Enabled = true;
                        lblStatus.Text = "설치 실패.";
                    }));
                }
            });
            t.Start();
        }

        [STAThread]
        public static void Main()
        {
            Application.EnableVisualStyles();
            Application.Run(new InstallerForm());
        }
    }
}
