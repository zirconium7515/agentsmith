@echo off
chcp 65001 >nul
setlocal EnableExtensions

if /I "%~1"=="RUN_FROM_TEMP" goto RUN_FROM_TEMP

for %%I in ("%~dp0.") do set "TARGET_DIR=%%~fI"

echo =======================================
echo AgentSmith 제거
echo =======================================
echo.
echo 아래 폴더와 그 안의 모든 파일을 삭제합니다.
echo "%TARGET_DIR%"
echo.
echo 이 작업은 되돌릴 수 없습니다.
echo.
set /p "confirm=계속하려면 Y를 입력하고 Enter를 누르세요: "

if /I not "%confirm%"=="Y" (
    echo 제거 작업을 취소했습니다.
    pause
    exit /b 0
)

set "TEMP_SCRIPT=%TEMP%\AgentSmith_Uninstall_%RANDOM%%RANDOM%.bat"
copy "%~f0" "%TEMP_SCRIPT%" >nul
if errorlevel 1 (
    echo 임시 제거 스크립트를 만들지 못했습니다.
    pause
    exit /b 1
)

echo 실행 중인 AgentSmith 프로세스를 종료합니다...
taskkill /F /IM AgentSmith.exe >nul 2>&1
taskkill /F /IM AgentSmith_Installer.exe >nul 2>&1
timeout /t 1 /nobreak >nul

start "" /D "%TEMP%" cmd /c ""%TEMP_SCRIPT%" RUN_FROM_TEMP "%TARGET_DIR%""
exit /b 0

:RUN_FROM_TEMP
set "TARGET_DIR=%~2"
cd /d "%TEMP%"

if "%TARGET_DIR%"=="" (
    echo [오류] 삭제 대상 폴더가 비어 있습니다.
    goto END_FAILED
)

for %%I in ("%TARGET_DIR%") do set "TARGET_DIR=%%~fI"
for %%I in ("%TARGET_DIR%") do set "TARGET_ROOT=%%~dI\"

if /I "%TARGET_DIR%"=="%TARGET_ROOT%" (
    echo [오류] 드라이브 루트는 삭제할 수 없습니다: "%TARGET_DIR%"
    goto END_FAILED
)

echo AgentSmith 폴더를 삭제하는 중입니다...
echo "%TARGET_DIR%"

set "MAX_RETRIES=5"
set /a attempt=0

:DELETE_LOOP
set /a attempt+=1
set "AGENTSMITH_TARGET_DIR=%TARGET_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$target=$env:AGENTSMITH_TARGET_DIR; if ([string]::IsNullOrWhiteSpace($target)) { exit 10 }; if (-not (Test-Path -LiteralPath $target)) { exit 0 }; Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop"

if %ERRORLEVEL% EQU 0 (
    echo 제거가 완료되었습니다.
    goto CLEANUP
)

rd /s /q "%TARGET_DIR%" >nul 2>&1
if not exist "%TARGET_DIR%" (
    echo 제거가 완료되었습니다.
    goto CLEANUP
)

if %attempt% LSS %MAX_RETRIES% (
    echo [경고] 폴더가 아직 사용 중입니다. %attempt%/%MAX_RETRIES% 재시도 중...
    timeout /t 2 /nobreak >nul
    goto DELETE_LOOP
)

echo [오류] 폴더 삭제에 실패했습니다.
echo 다음 항목을 확인한 뒤 다시 실행하세요.
echo 1. AgentSmith 또는 설치기 창이 열려 있는지 확인
echo 2. 파일 탐색기, 터미널, 에디터가 설치 폴더를 열고 있는지 확인
echo 3. Google Drive 동기화가 파일을 잡고 있는지 확인
echo 4. 관리자 권한이 필요한지 확인
goto END_FAILED

:CLEANUP
set "AGENTSMITH_TEMP_SCRIPT=%~f0"
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Start-Sleep -Seconds 1; Remove-Item -LiteralPath $env:AGENTSMITH_TEMP_SCRIPT -Force -ErrorAction SilentlyContinue"
exit /b 0

:END_FAILED
pause
set "AGENTSMITH_TEMP_SCRIPT=%~f0"
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Start-Sleep -Seconds 1; Remove-Item -LiteralPath $env:AGENTSMITH_TEMP_SCRIPT -Force -ErrorAction SilentlyContinue"
exit /b 1
