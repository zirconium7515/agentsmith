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
:: 자신을 포함한 부모 폴더(agentsmith)의 전체 경로 확보
set "TARGET_DIR=%CD%"

:: 자신을 임시 폴더(TEMP)로 복사 (실행 중인 폴더는 삭제 불가하기 때문)
copy "%~f0" "%TEMP%\AgentSmith_Uninstall.bat" >nul

:: 임시 폴더의 스크립트를 별도 프로세스로 실행하고, 현재 스크립트는 즉시 종료
start "" cmd /c "%TEMP%\AgentSmith_Uninstall.bat" RUN_FROM_TEMP "%TARGET_DIR%"
exit

:DeleteFolder
set "TARGET_DIR=%~2"
echo.
echo [진행] 실행 중인 앱을 종료하는 중입니다...
taskkill /f /im AgentSmith.exe >nul 2>&1
taskkill /f /im AgentSmith_Installer.exe >nul 2>&1
echo [진행] 앱 종료 및 폴더 잠금을 해제하는 중입니다 (2초 대기)...
timeout /t 2 /nobreak >nul

echo [진행] 폴더 내 읽기 전용 속성을 해제하고 있습니다 (시간이 소요될 수 있습니다)...
attrib -r -s -h "%TARGET_DIR%\*.*" /s /d >nul 2>&1

echo [진행] %TARGET_DIR% 폴더를 삭제하고 있습니다...
rmdir /s /q "%TARGET_DIR%"

echo [완료] AgentSmith가 PC에서 완전히 삭제되었습니다.
echo 3초 뒤 이 창은 자동으로 닫힙니다.
timeout /t 3 /nobreak >nul
:: 임시 폴더에 복사된 자신도 스스로 삭제
del "%~f0"
exit
