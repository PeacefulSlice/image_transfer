@echo off
REM ================================
REM Quick setup for the project
REM - creates venv (.venv) if missing
REM - installs requirements
REM ================================

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv" (
  echo [INFO] Creating venv in .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. Check Python installation.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate venv.
  pause
  exit /b 1
)

if not exist "requirements.txt" (
  echo [WARN] requirements.txt not found. Creating minimal one...
  (
    echo pillow
    echo pytest
    echo pytest-cov
    echo pytest-timeout
  ) > requirements.txt
)

echo [INFO] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed.
  pause
  exit /b 1
)

echo.
echo [INFO] Done.
echo Next:
echo  1) run_receiver.bat  (keep it open)
echo  2) run_sender.bat "C:\path\to\photo.jpg"
echo  3) run_tests.bat
pause >nul
