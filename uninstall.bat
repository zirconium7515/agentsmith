@echo off
@chcp 65001 >nul

:: ------------------------------------------------------------
:: AgentSmith 완전 삭제 스크립트
::   1) 현재 스크립트가 위치한 폴더를 정확히 파악
::   2) AgentSmith·Installer·Python 등 관련 프로세스 강제 종료
::   3) 파일 속성(읽기/숨김/시스템) 모두 해제
::   4) 작업 디렉터리를 TEMP 로 이동해 폴더 잠금 해제
::   5) PowerShell 로 재귀 강제 삭제 (최대 5회 재시도)
::   6) 실패 시 cmd rd 로 재시도
::   7) 그래도 안되면 최종 삭제 배치파일을 TEMP 에서 실행
::   8) 성공 시 스크립트 자체 삭제
:: ------------------------------------------------------------

rem ----- 1. 삭제 대상 폴더 경로 확보 (스크립트가 위치한 폴더) -----
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

rem ----- 2. 사용자 확인 -----
echo 이 작업은 "%TARGET_DIR%" 폴더와 그 안의 모든 파일을
echo 영구적으로 삭제합니다.
echo.
set /p "confirm=계속하려면 Y 를 입력하고 ENTER 키를 누르세요: "
if /I not "%confirm%"=="Y" (
    echo 작업이 취소되었습니다.
    pause
    exit /b
)

rem ----- 3. 관련 프로세스 강제 종료 -----
for %%P in (AgentSmith.exe AgentSmith_Installer.exe python.exe) do (
    taskkill /F /IM %%P >nul 2>&1
)
timeout /t 2 /nobreak >nul

rem ----- 4. 스크립트를 TEMP 로 복사하고, 복사본 실행 -----
copy "%~f0" "%TEMP%\\AgentSmith_Uninstall_Temp.bat" >nul
start "" cmd /c "%TEMP%\\AgentSmith_Uninstall_Temp.bat" RUN_FROM_TEMP "%TARGET_DIR%"
exit /b

rem ==============================================================
rem === 아래 코드는 TEMP 로 복사된 파일이 RUN_FROM_TEMP 플래그와 함께 실행될 때만 동작합니다 ===
rem ==============================================================

if "%~1" NEQ "RUN_FROM_TEMP" goto :eof
set "TARGET_DIR=%~2"

rem ----- 5. 작업 디렉터리를 TEMP 로 이동 (삭제 대상 폴더가 현재 작업 폴더가 되지 않도록) -----
cd /d "%TEMP%"

rem ----- 6. 폴더 삭제 (PowerShell) + 재시도 루프 -----
set "MAX_RETRIES=5"
set /a attempt=0
:DELETE_LOOP
powershell -NoProfile -Command "Remove-Item -LiteralPath '%TARGET_DIR%' -Recurse -Force -ErrorAction Stop"
if %ERRORLEVEL% EQU 0 (
    echo PowerShell 로 폴더 삭제 성공.
    goto CLEANUP
)

rem ----- 7. fallback: cmd rd -----
rd /s /q "%TARGET_DIR%" >nul 2>&1
if not exist "%TARGET_DIR%" (
    echo cmd rd 로 폴더 삭제 성공.
    goto CLEANUP
)

rem ----- 8. 재시도 로직 -----
set /a attempt+=1
if %attempt% LSS %MAX_RETRIES% (
    echo [경고] 폴더가 아직 사용 중입니다. %attempt%번째 재시도 중…
    timeout /t 3 /nobreak >nul
    goto DELETE_LOOP
) else (
    rem ----- 9. 최종 삭제 배치 파일 생성 및 실행 -----
    echo [오류] 폴더 삭제에 실패했습니다. 최종 삭제 배치를 실행합니다.
    (
        echo @echo off
        echo timeout /t 2 /nobreak >nul
        echo rd /s /q "%TARGET_DIR%" >nul 2>&1
        echo del "%%~f0" >nul 2>&1
    ) > "%TEMP%\\AgentSmith_FinalDelete.bat"
    start "" cmd /c "%TEMP%\\AgentSmith_FinalDelete.bat"
    goto END
)

rem ----- 10. 성공 시 스크립트 자체 삭제 -----
:CLEANUP
 echo 폴더 삭제가 완료되었습니다.
 del "%~f0" >nul 2>&1
 exit /b

:END
 echo 최종 삭제가 완료되지 않았습니다. 아래 항목을 확인하고 다시 시도하세요.
 echo   1) 구글 드라이브 / OneDrive 동기화 중
 echo   2) 파일 탐색기, VS Code 등에서 폴더가 열려 있음
 echo   3) 남아있는 백그라운드 프로세스
 echo   4) 관리자 권한 부족
 pause
 del "%~f0" >nul 2>&1
 exit /b
