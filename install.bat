@echo off
chcp 65001 >nul
echo ==========================================
echo AgentSmith 자동 설치 프로그램
echo ==========================================
echo.

:: 1. Git 설치 여부 확인
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [에러] Git이 설치되어 있지 않거나 환경 변수에 등록되지 않았습니다.
    echo https://git-scm.com/ 에서 Git을 먼저 설치해 주세요.
    pause
    exit /b
)

:: 2. Python 설치 여부 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [에러] Python이 설치되어 있지 않거나 환경 변수에 등록되지 않았습니다.
    echo https://www.python.org/ 에서 Python을 먼저 설치해 주세요. (설치 시 'Add Python to PATH' 체크 필수)
    pause
    exit /b
)

echo [진행] 깃허브에서 AgentSmith 최신 버전을 다운로드(Clone) 합니다...
git clone https://github.com/zirconium7515/agentsmith.git

if not exist agentsmith (
    echo [에러] 다운로드에 실패했습니다. 인터넷 연결이나 권한을 확인해 주세요.
    pause
    exit /b
)

echo [완료] 다운로드 완료! 자동 빌드 스크립트를 실행합니다...
cd agentsmith

:: 3. 초기 빌드 스크립트 실행
start update_and_build.bat
exit
