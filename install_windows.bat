@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo Object Tracking - Windows setup
echo ==========================================
echo.

python -m pip install --upgrade pip
if errorlevel 1 goto fail

python -m pip install -r requirements.txt
if errorlevel 1 goto fail

if exist "detect.tflite" if exist "James.mp4" goto assets_ok

echo.
echo [INFO] Model/sample assets are missing.
echo [INFO] Downloading them now...
python download_assets.py
if errorlevel 1 goto fail

:assets_ok
echo.
echo Setup completed.
echo Run: run_windows.bat
pause
exit /b 0

:fail
echo.
echo Setup failed. Check the Python interpreter used by this terminal.
pause
exit /b 1
