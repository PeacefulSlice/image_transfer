@echo off
REM ================================
REM Run Sender (client) in CMD
REM ================================

REM --- Change this if your project path is different ---
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate venv. Make sure .venv exists: python -m venv .venv
  pause
  exit /b 1
)

set "PYTHONPATH=src"

REM --- Set your photo path here OR pass it as first argument ---
REM Example:
REM set "PHOTO_PATH=C:\Users\Andrii\Pictures\photo.jpg"
set "PHOTO_PATH=%~1"

if "%PHOTO_PATH%"=="" (
  echo [ERROR] No photo path provided.
  echo Usage:
  echo   run_sender.bat "C:\path\to\photo.jpg"
  echo Or edit PHOTO_PATH inside this file.
  pause
  exit /b 1
)

if not exist "%PHOTO_PATH%" (
  echo [ERROR] File not found: %PHOTO_PATH%
  pause
  exit /b 1
)

echo [INFO] Sending: %PHOTO_PATH%
python -m imgtx.cli send --host 127.0.0.1 --port 5000 --file "%PHOTO_PATH%"

echo.
echo [INFO] Sender finished. Press any key to close.
pause >nul
