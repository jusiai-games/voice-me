@echo off
chcp 65001 >nul
rem 대본을 내 목소리로 읽어 output 폴더에 wav 로 저장합니다.
call "%~dp0_launch.bat" src\main.py %*
