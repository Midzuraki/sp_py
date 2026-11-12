@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [setup] Virtual environment not found, creating...
    where python >nul 2>nul
    if errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto :error
    "%VENV_PY%" -m pip install -e .
    if errorlevel 1 goto :error
)

"%VENV_PY%" -m main
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo [error] Something went wrong. Check that Python 3.9+ is installed and added to PATH.
pause