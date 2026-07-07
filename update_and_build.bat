@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================
echo AgentSmith 자동 업데이트 (자가 복구 모드)
echo =======================================

echo 1. 기존 AgentSmith 프로세스 종료...
taskkill /F /IM AgentSmith.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo 2. 로컬 빌드 잔재 및 충돌 요소 청소...
git clean -fd dist >nul 2>&1
git checkout -- dist >nul 2>&1

echo 3. GitHub에서 최신 컴파일 본 가져오는 중...
git fetch origin >nul 2>&1
git reset --hard origin/master

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
