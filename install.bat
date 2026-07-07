@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ==========================================
echo AgentSmith 무인 자동 설치 프로그램
echo ==========================================
echo.

:: 1. 윈도우 폴더 선택 창(GUI) 띄우기
echo [안내] 팝업창에서 AgentSmith를 설치할 폴더를 선택해 주세요.
echo (팝업창이 화면 뒤에 가려져 있을 수 있으니 작업 표시줄을 확인하세요.)
set "INSTALL_DIR="
for /f "usebackq tokens=*" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.windows.forms | Out-Null; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'AgentSmith를 설치할 최상위 폴더를 선택하세요 (이 폴더 안에 agentsmith 폴더가 생성됩니다)'; $f.ShowNewFolderButton = $true; $f.RootFolder = 'MyComputer'; if($f.ShowDialog() -eq 'OK'){ $f.SelectedPath } else { 'CANCEL' }"`) do set "INSTALL_DIR=%%I"

if "%INSTALL_DIR%"=="CANCEL" (
    echo [취소] 폴더 선택이 취소되었습니다. 설치를 종료합니다.
    pause
    exit /b
)
if "%INSTALL_DIR%"=="" (
    echo [취소] 폴더 선택 창에서 오류가 발생했습니다. 설치를 종료합니다.
    pause
    exit /b
)

echo.
echo [확인] 선택된 설치 경로: %INSTALL_DIR%\agentsmith
echo.

set "NEEDS_REFRESH=0"

:: 2. Git 확인 및 설치
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [진행] Git이 발견되지 않았습니다. 자동으로 설치를 시작합니다...
    winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements --silent
    set "NEEDS_REFRESH=1"
) else (
    echo [OK] Git이 이미 설치되어 있습니다.
)

:: 3. Python 확인 및 설치
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [진행] Python이 발견되지 않았습니다. 자동으로 설치를 시작합니다...
    winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements --silent
    set "NEEDS_REFRESH=1"
) else (
    echo [OK] Python이 이미 설치되어 있습니다.
)

:: 4. 환경 변수(PATH) 실시간 새로고침
if "!NEEDS_REFRESH!"=="1" (
    echo [진행] 시스템 환경 변수를 동기화하고 있습니다...
    for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "syspath=%%B"
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "userpath=%%B"
    set "PATH=!syspath!;!userpath!"
)

echo.
echo ==========================================
echo [진행] 지정된 폴더에 소스코드 다운로드 및 앱 빌드를 시작합니다...
echo ==========================================

:: 5. 지정된 경로로 이동하여 Github Clone
cd /d "%INSTALL_DIR%"
if not exist "agentsmith" (
    git clone https://github.com/zirconium7515/agentsmith.git
    if %errorlevel% neq 0 (
        echo [에러] Git 다운로드에 실패했습니다. (권한 문제일 수 있습니다)
        pause
        exit /b
    )
) else (
    echo [안내] %INSTALL_DIR%\agentsmith 폴더가 이미 존재합니다. 기존 폴더를 덮어쓰지 않고 진입합니다.
)

cd agentsmith

:: 6. 빌드 스크립트 백그라운드 실행
echo [완료] 모든 준비가 끝났습니다! 빌드를 시작하고 이 창을 닫습니다.
start update_and_build.bat
exit
