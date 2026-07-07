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

        public InstallerForm()
        {
            this.Text = "AgentSmith Installer";
            this.Size = new Size(400, 250);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;

            Label lblTitle = new Label();
            lblTitle.Text = "AgentSmith Setup";
            lblTitle.Font = new Font("Arial", 14, FontStyle.Bold);
            lblTitle.Location = new Point(110, 20);
            lblTitle.AutoSize = true;
            this.Controls.Add(lblTitle);

            Label lblDesc = new Label();
            lblDesc.Text = "설치할 경로를 지정해 주세요:";
            lblDesc.Location = new Point(20, 60);
            lblDesc.AutoSize = true;
            this.Controls.Add(lblDesc);

            txtPath = new TextBox();
            txtPath.Text = @"C:\AgentSmith";
            txtPath.Location = new Point(20, 80);
            txtPath.Width = 260;
            this.Controls.Add(txtPath);

            btnBrowse = new Button();
            btnBrowse.Text = "찾아보기...";
            btnBrowse.Location = new Point(290, 78);
            btnBrowse.Click += BtnBrowse_Click;
            this.Controls.Add(btnBrowse);

            lblStatus = new Label();
            lblStatus.Text = "설치 준비 완료.";
            lblStatus.ForeColor = Color.Gray;
            lblStatus.Location = new Point(20, 115);
            lblStatus.AutoSize = true;
            this.Controls.Add(lblStatus);

            progressBar = new ProgressBar();
            progressBar.Style = ProgressBarStyle.Marquee;
            progressBar.Location = new Point(20, 135);
            progressBar.Width = 345;
            progressBar.Height = 15;
            progressBar.Visible = false;
            this.Controls.Add(progressBar);

            btnInstall = new Button();
            btnInstall.Text = "설치 시작";
            btnInstall.Location = new Point(140, 165);
            btnInstall.Width = 100;
            btnInstall.Height = 30;
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
        }

        private void RunCommand(string fileName, string args)
        {
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = fileName;
            psi.Arguments = args;
            psi.CreateNoWindow = true;
            psi.UseShellExecute = false;
            Process p = Process.Start(psi);
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

            Thread t = new Thread(() =>
            {
                try
                {
                    if (!Directory.Exists(installDir))
                    {
                        Directory.CreateDirectory(installDir);
                    }

                    Log("Git 설치 여부 확인 중...");
                    if (!CheckCommand("git"))
                    {
                        Log("Git 무인 설치 중 (시간이 소요될 수 있습니다)...");
                        RunCommand("winget", "install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements --silent");
                    }

                    Log("Python 설치 여부 확인 중...");
                    if (!CheckCommand("python"))
                    {
                        Log("Python 무인 설치 중 (시간이 소요될 수 있습니다)...");
                        RunCommand("winget", "install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements --silent");
                    }

                    Log("최신 소스코드 다운로드 중 (Git Clone)...");
                    Directory.SetCurrentDirectory(installDir);
                    if (!Directory.Exists(".git"))
                    {
                        RunCommand("git", "clone https://github.com/zirconium7515/agentsmith.git .");
                    }

                    Log("빌드 스크립트 실행 준비 중...");
                    if (File.Exists("update_and_build.bat"))
                    {
                        ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c start update_and_build.bat");
                        psi.CreateNoWindow = true;
                        psi.UseShellExecute = false;
                        Process.Start(psi);
                    }
                    else
                    {
                        MessageBox.Show("빌드 스크립트를 찾을 수 없습니다!", "오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }

                    this.Invoke(new Action(() => {
                        progressBar.Visible = false;
                        lblStatus.Text = "초기 셋업 완료!";
                        MessageBox.Show("AgentSmith 다운로드가 완료되었습니다!\n터미널 창에서 초기 빌드가 진행됩니다.", "설치 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        Application.Exit();
                    }));
                }
                catch (Exception ex)
                {
                    this.Invoke(new Action(() => {
                        progressBar.Visible = false;
                        MessageBox.Show("설치 중 오류가 발생했습니다:\n" + ex.Message, "오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
