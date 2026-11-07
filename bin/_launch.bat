@echo off
chcp 65001 >nul
rem 다른 실행 스크립트가 공통으로 사용합니다. 직접 실행할 필요는 없습니다.
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo [오류] 환경이 준비되지 않았습니다. 먼저 bin 폴더의 setup.bat 을 실행해 주세요.
    pause
    exit /b 1
)

set "PYTHONUTF8=1"
".venv\Scripts\python.exe" %*
set "code=%errorlevel%"
echo.
pause
exit /b %code%
