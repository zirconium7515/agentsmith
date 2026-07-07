@echo off
chcp 65001 >nul
echo =======================================
echo AgentSmith 자동 업데이트
echo =======================================

echo 1. GitHub에서 최신 코드를 가져오는 중...
git pull origin master

echo 2. 필요한 패키지를 설치하는 중...
pip install -r requirements.txt
pip install pyinstaller

echo 3. AgentSmith.exe를 빌드하는 중...
python -m PyInstaller --noconfirm --onedir --windowed --name "AgentSmith" main.py

echo =======================================
echo 업데이트 및 빌드 완료!

if "%~1"=="--no-start" (
    echo 빌드가 정상적으로 완료되었습니다.
    exit /b
)

echo AgentSmith를 다시 시작하는 중...
echo =======================================

start "" "dist\AgentSmith\AgentSmith.exe"
exit
