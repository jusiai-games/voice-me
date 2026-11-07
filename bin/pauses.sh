#!/usr/bin/env bash
# output 폴더의 wav 에서 긴 쉼을 줄여 output/tight 에 저장합니다.
exec bash "$(dirname "$0")/_launch.sh" src/pauses.py "$@"
