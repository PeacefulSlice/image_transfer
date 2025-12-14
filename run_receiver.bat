@echo off
REM ================================
REM Run Receiver (server) in CMD
REM ================================

REM --- Change this if your project path is different ---
set "PROJECT_DIR=%~dp0"

REM If you place this .bat inside your project root, it will work automatically.
REM Otherwise set PROJECT_DIR manually, e.g.:
REM set "PROJECT_DIR=C:\Programming\image_transfer\"

cd /d "%PROJECT_DIR%"

REM --- Activate venv ---
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate venv. Make sure .venv exists: python -m venv .venv
  pause
  exit /b 1
)

REM --- Make src importable ---
set "PYTHONPATH=src"

REM --- Ensure output dir exists ---
if not exist "outputs\received" mkdir "outputs\received"

echo [INFO] Starting RECEIVER on 127.0.0.1:5000 ...
echo [INFO] Waiting for a sender connection...
python -m imgtx.cli recv --host 127.0.0.1 --port 5000 --out outputs\received

echo.
echo [INFO] Receiver finished (serve_once). Press any key to close.
pause >nul
