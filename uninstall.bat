@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

if "%~1"=="RUN_FROM_TEMP" goto DeleteFolder

echo ==========================================
echo AgentSmith 완전 삭제 프로그램
echo ==========================================
echo.
echo 정말로 AgentSmith를 완전히 삭제하시겠습니까?
echo 이 작업은 취소할 수 없으며, 모든 소스코드와 설정 파일이 영구 삭제됩니다.
echo.
set /p "confirm=삭제하려면 Y를 누르고 엔터를 치세요 (Y/N): "
if /i "%confirm%"=="Y" goto StartUninstall

echo 삭제가 취소되었습니다.
pause
exit /b

:StartUninstall
:: 자신을 포함한 부모 폴더(agentsmith)의 전체 경로 확보 (%CD% 대신 %~dp0 사용)
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

:: 자신을 임시 폴더(TEMP)로 복사 (실행 중인 폴더는 삭제 불가하기 때문)
copy "%~f0" "%TEMP%\AgentSmith_Uninstall.bat" >nul

:: 임시 폴더의 스크립트를 별도 프로세스로 실행하고, 현재 스크립트는 즉시 종료
start "" cmd /c "%TEMP%\AgentSmith_Uninstall.bat" RUN_FROM_TEMP "%TARGET_DIR%"
exit

:DeleteFolder
set "TARGET_DIR=%~2"
echo.
:: 현재 스크립트(cmd.exe)의 작업 경로를 임시 폴더로 이동하여 삭제할 폴더의 잠금을 해제합니다.
cd /d "%TEMP%"

echo [진행] 실행 중인 앱을 종료하는 중입니다...
taskkill /f /im AgentSmith.exe >nul 2>&1
taskkill /f /im AgentSmith_Installer.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo [진행] 앱 종료 및 폴더 잠금을 해제하는 중입니다 (2초 대기)...
timeout /t 2 /nobreak >nul

echo [진행] 폴더 내 읽기 전용 속성을 해제하고 있습니다 (시간이 소요될 수 있습니다)...
attrib -r -s -h "%TARGET_DIR%\*.*" /s /d >nul 2>&1

echo [진행] %TARGET_DIR% 폴더 삭제를 시도합니다...
set RETRY=0

:RetryLoop
rmdir /s /q "%TARGET_DIR%"
if exist "%TARGET_DIR%" (
    set /a RETRY+=1
    if !RETRY! lss 5 (
        echo [경고] 구글 드라이브 동기화 또는 다른 프로세스 때문에 폴더가 잠겨 있습니다. 3초 후 다시 시도합니다... ^(!RETRY!/5^)
        timeout /t 3 /nobreak >nul
        goto RetryLoop
    ) else (
        echo.
        echo ==========================================
        echo [오류] 삭제에 실패했습니다!
        echo ==========================================
        echo 누군가 폴더를 꽉 잡고 놓아주지 않고 있습니다.
        echo 다음 중 하나가 원인일 확률이 99%% 입니다:
        echo 1. 구글 드라이브가 현재 이 폴더를 동기화 중임
        echo 2. VS Code 등 코드 에디터가 이 폴더를 열고 있음
        echo 3. 백그라운드에 파이썬 프로세스가 살아있음
        echo.
        echo 폴더 창이나 에디터를 모두 닫고 윈도우를 재부팅하신 후 다시 시도해 주세요.
        echo (이 창은 아무 키나 누르면 닫힙니다.)
        pause >nul
        del "%~f0"
        exit
    )
)

echo.
echo ==========================================
echo [완료] AgentSmith가 PC에서 완전히 삭제되었습니다!
echo ==========================================
echo (이 창은 아무 키나 누르면 닫힙니다.)
pause >nul
:: 임시 폴더에 복사된 자신도 스스로 삭제
del "%~f0"
exit
