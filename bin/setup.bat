@echo off
chcp 65001 >nul
rem 처음 한 번만 실행합니다. 파이썬 가상환경을 만들고 필요한 패키지를 설치합니다.
setlocal
cd /d "%~dp0.."

rem NVIDIA GPU 확인
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [오류] NVIDIA GPU 를 찾지 못했습니다. 이 프로그램은 NVIDIA GPU 가 있는 PC 에서만 실행할 수 있습니다.
    goto end_fail
)

rem Python 3.12 찾기
set "python="
py -3.12 --version >nul 2>&1 && set "python=py -3.12"
if not defined python (
    python --version 2>nul | findstr /b /c:"Python 3.12." >nul && set "python=python"
)
if not defined python (
    echo [오류] Python 3.12 가 필요합니다. https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행해 주세요.
    goto end_fail
)

if not exist ".venv\Scripts\python.exe" (
    echo 가상환경을 만드는 중...
    %python% -m venv .venv || goto fail
)

echo 패키지를 설치하는 중... 인터넷 속도에 따라 수십 분 걸릴 수 있습니다.
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto fail

echo.
echo 준비가 끝났습니다. README.md 의 '내 파일 준비하기'를 따라 주세요.
pause
exit /b 0

:fail
echo.
echo [오류] 설치하지 못했습니다. 위의 메시지를 확인해 주세요.

:end_fail
pause
exit /b 1
