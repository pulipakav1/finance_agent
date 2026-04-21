# Absolute --reload-exclude so venv is actually ignored on Windows (relative "venv" does not match).
Set-Location $PSScriptRoot
$venv = Join-Path $PSScriptRoot "venv"
$src = Join-Path $PSScriptRoot "src"
$cfg = Join-Path $PSScriptRoot "config"
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000 --reload-dir $src --reload-dir $cfg --reload-exclude $venv
