@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo PC USB Object Tracking
echo ==========================================
echo Q or ESC : Exit
echo.

set "PYEXE="

rem Use "if not errorlevel 1": it is evaluated at run time, unlike the errorlevel variable inside a ( ) block.
where py >nul 2>nul
if not errorlevel 1 (
    py -3.13 -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PYEXE=py -3.13"
)

if not defined PYEXE (
    if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
        set "PYEXE=%LocalAppData%\Programs\Python\Python313\python.exe"
    )
)

if not defined PYEXE (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys" >nul 2>nul
        if not errorlevel 1 set "PYEXE=python"
    )
)

if not defined PYEXE (
    echo [ERROR] Python was not found.
    echo Run install_windows.bat first.
    pause
    exit /b 1
)

if not exist "detect.tflite" (
    echo [INFO] detect.tflite is missing. Downloading assets...
    %PYEXE% download_assets.py
    if errorlevel 1 goto fail
)

%PYEXE% object_tracking_pc.py
if errorlevel 1 goto fail
exit /b 0

:fail
echo.
echo [ERROR] Program exited with an error.
echo Run install_windows.bat again if dependencies are missing.
pause
exit /b 1
