#!/usr/bin/env bash
# 대본을 내 목소리로 읽어 output 폴더에 wav 로 저장합니다.
exec bash "$(dirname "$0")/_launch.sh" src/main.py "$@"
