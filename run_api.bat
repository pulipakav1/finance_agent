@echo off
REM Use absolute paths for --reload-exclude (relative "venv" fails on Windows vs absolute path.parents).
cd /d "%~dp0"
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000 --reload-dir "%~dp0src" --reload-dir "%~dp0config" --reload-exclude "%~dp0venv"
