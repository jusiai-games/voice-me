@echo off
chcp 65001 >nul
rem output 폴더의 wav 에서 잡음을 줄여 output/clean 에 저장합니다.
call "%~dp0_launch.bat" src\denoise.py %*
