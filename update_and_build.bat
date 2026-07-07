@echo off
chcp 65001 >nul
echo =======================================
echo AgentSmith 자동 업데이트
echo =======================================

echo 1. 기존 AgentSmith 프로세스 종료...
taskkill /F /IM AgentSmith.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo 2. GitHub에서 최신 코드를 가져오는 중...
git pull origin master

echo 3. 필요한 패키지를 설치하는 중...
pip install -r requirements.txt
pip install pyinstaller

echo 4. 빌드 캐시 및 이전 빌드 삭제...
if exist build rd /s /q build
if exist dist rd /s /q dist

echo 5. AgentSmith.exe를 빌드하는 중...
python -m PyInstaller --clean --noconfirm --onedir --windowed --name "AgentSmith" main.py

if %ERRORLEVEL% NEQ 0 (
    echo [오류] 빌드에 실패했습니다. 이전 프로세스가 완전히 종료되었는지 확인하세요.
    pause
    exit /b 1
)

echo =======================================
echo 업데이트 및 빌드 완료!

if "%~1"=="--no-start" (
    echo 빌드가 정상적으로 완료되었습니다.
    exit /b 0
)

echo AgentSmith를 다시 시작하는 중...
echo =======================================

start "" "dist\AgentSmith\AgentSmith.exe"
exit /b 0
