@echo off
REM === Create/Activate venv and run app ===
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist .venv (
    py -3 -m venv .venv
)
call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m app.main

