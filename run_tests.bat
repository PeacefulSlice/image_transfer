@echo off
REM ================================
REM Run tests (pytest) in CMD
REM ================================

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate venv. Make sure .venv exists: python -m venv .venv
  pause
  exit /b 1
)

set "PYTHONPATH=src"

echo [INFO] Running pytest...
pytest -q

echo.
echo [INFO] Coverage report...
pytest --cov=imgtx --cov-report=term-missing

echo.
echo [INFO] Tests finished. Press any key to close.
pause >nul
