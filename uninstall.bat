@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ------------------------------------------------------------
:: AgentSmith 완전 삭제 스크립트
::   - 어디서 실행해도 현재 스크립트가 위치한 폴더를 정확히 찾음
::   - 실행 중인 AgentSmith 관련 프로세스를 강제 종료
::   - 모든 파일 속성(읽기 전용·숨김·시스템) 해제
::   - PowerShell 로 재귀 강제 삭제 (최대 5회 재시도)
::   - 실패 시 cmd.exe 가 작업 폴더를 점유하고 있으면 종료
::   - 성공 시 스크립트 자체 삭제
:: ------------------------------------------------------------

rem ----- 1. 설치 폴더 경로 확보 -----
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo This will permanently delete AgentSmith from:
echo   "%INSTALL_DIR%"
set /p "confirm=Type Y and press ENTER to continue: "
if /I not "%confirm%"=="Y" (
    echo Cancellation requested. Exiting.
    pause
    exit /b
)

rem ----- 2. 실행 중인 프로세스 강제 종료 -----
for %%P in (AgentSmith.exe AgentSmith_Installer.exe python.exe) do (
    taskkill /F /IM %%P >nul 2>&1
)
timeout /t 2 /nobreak >nul

rem ----- 3. 파일 속성 해제 -----
attrib -R -A -S -H "%INSTALL_DIR%\*" /S /D >nul 2>&1

rem ----- 4. 폴더 삭제 (PowerShell) + 재시도 루프 -----
set "MAX_RETRIES=5"
set /a attempt=0
:DELETE_LOOP
powershell -NoProfile -Command "Remove-Item -LiteralPath '%INSTALL_DIR%' -Recurse -Force -ErrorAction Stop"
if %ERRORLEVEL% EQU 0 (
    echo Deletion succeeded via PowerShell.
    goto CLEANUP
)
rem ----- 5. fallback: cmd rd -----
rd /s /q "%INSTALL_DIR%" >nul 2>&1
if not exist "%INSTALL_DIR%" (
    echo Deletion succeeded via fallback.
    goto CLEANUP
)
rem ----- 6. 추가 프로세스 종료 (cmd.exe 가 작업 폴더 점유) -----
for /f "tokens=2 delims=," %%I in ('wmic process where "Name='cmd.exe' and CommandLine like '%%^%INSTALL_DIR%%'" get ProcessId /format:csv ^| findstr /v "Node"') do (
    taskkill /F /PID %%I >nul 2>&1
)
set /a attempt+=1
if %attempt% LEQ %MAX_RETRIES% (
    echo [경고] 폴더가 아직 사용 중입니다. %attempt%번째 재시도 중...
    timeout /t 3 /nobreak >nul
    goto DELETE_LOOP
) else (
    echo ====================================================
    echo [ERROR] 폴더 삭제에 실패했습니다. 최대 시도 횟수(%MAX_RETRIES%)를 초과했습니다.
    echo 가능한 원인:
    echo   1. 구글 드라이브 / OneDrive 동기화 중
    echo   2. 파일 탐색기, VS Code 등에서 폴더가 열려 있음
    echo   3. 남아있는 백그라운드 프로세스
    echo   4. 시스템 권한 문제
    pause
    goto END
)

:CLEANUP
rem ----- 7. 스크립트 자체 삭제 -----
del "%~f0" >nul 2>&1
exit /b

:END
exit /b
