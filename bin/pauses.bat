@echo off
chcp 65001 >nul
rem output 폴더의 wav 에서 긴 쉼을 줄여 output/tight 에 저장합니다.
call "%~dp0_launch.bat" src\pauses.py %*
