@echo off
REM No auto-reload — use after pip install or when you want a quiet server.
cd /d "%~dp0"
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
