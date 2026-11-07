#!/usr/bin/env bash
# 처음 한 번만 실행합니다. 파이썬 가상환경을 만들고 필요한 패키지를 설치합니다.
set -euo pipefail
cd "$(dirname "$0")/.."

# NVIDIA GPU 확인
if ! command -v nvidia-smi >/dev/null 2>&1 || ! nvidia-smi >/dev/null 2>&1; then
    echo "[오류] NVIDIA GPU 를 찾지 못했습니다. 이 프로그램은 NVIDIA GPU 가 있는 PC 에서만 실행할 수 있습니다."
    exit 1
fi

# Python 3.12 찾기
if command -v python3.12 >/dev/null 2>&1; then
    python=python3.12
elif command -v python3 >/dev/null 2>&1 && python3 --version | grep -q '^Python 3\.12\.'; then
    python=python3
else
    echo "[오류] Python 3.12 가 필요합니다. https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행해 주세요."
    exit 1
fi

if [ ! -x .venv/bin/python ]; then
    echo "가상환경을 만드는 중..."
    if ! "$python" -m venv .venv; then
        rm -rf .venv
        echo "[오류] 가상환경을 만들지 못했습니다. Ubuntu/Debian 이면 'sudo apt install python3.12-venv' 를 실행한 뒤 다시 시도해 주세요."
        exit 1
    fi
fi

echo "패키지를 설치하는 중... (인터넷 속도에 따라 수십 분 걸릴 수 있습니다)"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "준비가 끝났습니다. README.md 의 '내 파일 준비하기'를 따라 주세요."
