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

echo 3. 필요한 패키지를 설치하는 중...
pip install -r requirements.txt
pip install pyinstaller

echo 4. tkinter 설치 여부 검사 중...
python -c "import tkinter" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [오류] 현재 Python 환경에 tkinter가 설치되어 있지 않습니다.
    echo.
    echo Tkinter는 Python 표준 라이브러리로, Python 설치 시 tcl/tk and IDLE 옵션을 선택해야 설치됩니다.
    echo.
    echo 해결 방법:
    echo 1. Windows 제어판 - 프로그램 추가/제거에서 Python을 찾아 변경 또는 Modify 버튼을 누릅니다.
    echo 2. Modify를 클릭한 뒤, tcl/tk and IDLE 체크박스를 선택하고 설치를 완료하십시오.
    echo.
    pause
    exit /b 1
)

echo 5. 빌드 캐시 및 이전 빌드 삭제...
if exist build rd /s /q build
if exist dist rd /s /q dist

echo 6. AgentSmith.exe를 빌드하는 중...
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
