@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================
echo AgentSmith 자동 업데이트
echo =======================================

echo 1. 기존 AgentSmith 프로세스 종료...
taskkill /F /IM AgentSmith.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo 2. GitHub에서 최신 코드를 가져오는 중...
git pull origin master

echo =======================================
echo 업데이트 완료!

if "%~1"=="--no-start" (
    echo 업데이트가 정상적으로 완료되었습니다.
    exit /b 0
)

echo AgentSmith를 다시 시작하는 중...
echo =======================================

start "" "dist\AgentSmith\AgentSmith.exe"
exit /b 0
