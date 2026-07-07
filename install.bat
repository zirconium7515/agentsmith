@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ==========================================
echo AgentSmith 무인 자동 설치 프로그램
echo ==========================================
echo.

set "NEEDS_REFRESH=0"

:: 1. Git 확인 및 설치
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [진행] Git이 발견되지 않았습니다. 자동으로 설치를 시작합니다...
    winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements --silent
    set "NEEDS_REFRESH=1"
) else (
    echo [OK] Git이 이미 설치되어 있습니다.
)

:: 2. Python 확인 및 설치
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [진행] Python이 발견되지 않았습니다. 자동으로 설치를 시작합니다...
    winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements --silent
    set "NEEDS_REFRESH=1"
) else (
    echo [OK] Python이 이미 설치되어 있습니다.
)

:: 3. 환경 변수(PATH) 실시간 새로고침 (설치가 발생했을 경우에만)
if "!NEEDS_REFRESH!"=="1" (
    echo [진행] 시스템 환경 변수를 동기화하고 있습니다...
    :: 시스템 PATH 가져오기
    for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "syspath=%%B"
    :: 사용자 PATH 가져오기
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "userpath=%%B"
    :: 현재 세션 PATH 강제 업데이트
    set "PATH=!syspath!;!userpath!"
)

echo.
echo ==========================================
echo [진행] 소스코드 다운로드 및 앱 빌드를 시작합니다...
echo ==========================================

:: 4. Github Clone
if not exist "agentsmith" (
    git clone https://github.com/zirconium7515/agentsmith.git
    if %errorlevel% neq 0 (
        echo [에러] Git 다운로드에 실패했습니다.
        pause
        exit /b
    )
) else (
    echo [안내] agentsmith 폴더가 이미 존재합니다. 덮어쓰지 않고 진입합니다.
)

cd agentsmith

:: 5. 빌드 스크립트 백그라운드 실행
echo [완료] 모든 준비가 끝났습니다! 빌드를 시작하고 창을 닫습니다.
start update_and_build.bat
exit
