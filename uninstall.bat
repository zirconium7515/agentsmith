@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ------------------------------------------------------------
:: AgentSmith 완전 삭제 스크립트
::   - 어디서 실행해도 현재 스크립트가 위치한 폴더를 정확히 찾음
::   - 실행 중인 AgentSmith 관련 프로세스를 강제 종료
::   - 읽기 전용/숨김/시스템 속성을 모두 해제
::   - PowerShell 로 폴더를 강제 재귀 삭제 (최대 5번 재시도)
::   - 삭제 성공 시 스스로 파일을 지우고 종료
:: ------------------------------------------------------------

rem --- 1. 설치 폴더 경로 확보 (스크립트 자체가 있는 폴더) ---
set "INSTALL_DIR=%~dp0"
rem 제거할 때 뒤에 남는 역슬래시를 없앱니다
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo This will permanently delete AgentSmith from:
echo   "%INSTALL_DIR%"
set /p "confirm=Type Y and press ENTER to continue: "
if /I not "%confirm%"=="Y" (
    echo Cancellation requested. Exiting.
    pause
    exit /b
)

rem --- 2. 실행 중인 관련 프로세스 강제 종료 ---
for %%P in (AgentSmith.exe AgentSmith_Installer.exe python.exe) do (
    taskkill /F /IM %%P >nul 2>&1
)
timeout /t 2 /nobreak >nul

rem --- 3. 파일 속성 해제 (읽기 전용, 숨김, 시스템) ---
attrib -R -A -S -H "%INSTALL_DIR%\*" /S /D >nul 2>&1

rem --- 4. PowerShell 로 폴더 삭제, 최대 5회 재시도 ---
set "MAX_RETRIES=5"
set /a attempt=0
:DELETE_LOOP
powershell -NoProfile -Command "Remove-Item -LiteralPath '%INSTALL_DIR%' -Recurse -Force -ErrorAction Stop"
if %ERRORLEVEL% EQU 0 (
    echo Deletion succeeded.
    goto CLEANUP
)
set /a attempt+=1
if %attempt% LEQ %MAX_RETRIES% (
    echo Deletion attempt %attempt% failed, retrying in 3 seconds...
    timeout /t 3 /nobreak >nul
    goto DELETE_LOOP
)

rem --- 5. 모두 실패했을 경우 안내 ---
echo ====================================================
echo [ERROR] Could not delete the folder after %MAX_RETRIES% attempts.
echo Possible reasons:
echo   1. Google Drive / OneDrive 동기화가 진행 중
echo   2. VS Code, 파일 탐색기 등에서 폴더가 열려 있음
echo   3. 남아있는 백그라운드 프로세스
echo
echo Please close any programs that may lock the folder and run this script again.
pause
goto END

:CLEANUP
rem --- 6. 스크립트 자체 삭제 ---
del "%~f0" >nul 2>&1
exit /b

:END
exit /b
