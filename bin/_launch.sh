#!/usr/bin/env bash
# 다른 실행 스크립트가 공통으로 사용합니다. 직접 실행할 필요는 없습니다.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
    echo "[오류] 환경이 준비되지 않았습니다. 먼저 'bash bin/setup.sh' 를 실행해 주세요."
    exit 1
fi

exec .venv/bin/python "$@"
