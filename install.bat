@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ==========================================
echo AgentSmith 무인 자동 설치 프로그램
echo ==========================================
echo.

:: 1. 윈도우 폴더 선택 창(GUI) 띄우기
echo [안내] 팝업창에서 AgentSmith를 설치할 폴더를 선택해 주세요.
echo (팝업창이 뜨지 않는다면 화면 뒤나 아래 작업표시줄을 확인하세요.)

set "TEMP_FILE=%TEMP%\agentsmith_install_dir.txt"
if exist "%TEMP_FILE%" del "%TEMP_FILE%"

:: [버그 픽스] 한글 텍스트 바이트 정렬 문제로 인한 크래시를 막기 위해 영어 전용 인자 사용
powershell -STA -NoProfile -Command "Add-Type -AssemblyName System.windows.forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Please select the installation folder for AgentSmith'; $f.ShowNewFolderButton = $true; $f.RootFolder = 'MyComputer'; $form = New-Object System.Windows.Forms.Form; $form.TopMost = $true; if($f.ShowDialog($form) -eq 'OK'){ [IO.File]::WriteAllText($env:TEMP + '\agentsmith_install_dir.txt', $f.SelectedPath) } else { [IO.File]::WriteAllText($env:TEMP + '\agentsmith_install_dir.txt', 'CANCEL') }"

if not exist "%TEMP_FILE%" goto Cancelled

set /p INSTALL_DIR=<"%TEMP_FILE%"

if "%INSTALL_DIR%"=="CANCEL" goto Cancelled

echo.
echo [확인] 선택된 설치 경로: %INSTALL_DIR%\agentsmith
echo.

set "NEEDS_REFRESH=0"

:: 2. Git 확인 및 설치
git --version >nul 2>&1
if %errorlevel% equ 0 goto CheckPython

echo [진행] Git이 발견되지 않았습니다. 자동으로 설치를 시작합니다...
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements --silent
set "NEEDS_REFRESH=1"

:CheckPython
:: 3. Python 확인 및 설치
python --version >nul 2>&1
if %errorlevel% equ 0 goto CheckPath

echo [진행] Python이 발견되지 않았습니다. 자동으로 설치를 시작합니다...
winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements --silent
set "NEEDS_REFRESH=1"

:CheckPath
:: 4. 환경 변수(PATH) 실시간 새로고침
if "%NEEDS_REFRESH%"=="0" goto StartClone

echo [진행] 시스템 환경 변수를 동기화하고 있습니다...
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "syspath=%%B"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "userpath=%%B"
set "PATH=%syspath%;%userpath%"

:StartClone
echo.
echo ==========================================
echo [진행] 지정된 폴더에 소스코드 다운로드 및 앱 빌드를 시작합니다...
echo ==========================================

:: 5. 지정된 경로로 이동하여 Github Clone
cd /d "%INSTALL_DIR%"
if exist "agentsmith" goto RunBuild

git clone https://github.com/zirconium7515/agentsmith.git
if %errorlevel% equ 0 goto RunBuild

echo [에러] Git 다운로드에 실패했습니다. (권한 문제일 수 있습니다)
pause
exit /b

:RunBuild
cd agentsmith

:: 6. 빌드 스크립트 백그라운드 실행
echo [완료] 모든 준비가 끝났습니다! 빌드를 시작하고 이 창을 닫습니다.
start update_and_build.bat
exit

:Cancelled
echo [취소] 폴더 선택이 취소되었습니다. 설치를 종료합니다.
pause
exit /b
