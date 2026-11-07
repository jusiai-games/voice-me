#!/usr/bin/env bash
# output 폴더의 wav 에서 잡음을 줄여 output/clean 에 저장합니다.
exec bash "$(dirname "$0")/_launch.sh" src/denoise.py "$@"
