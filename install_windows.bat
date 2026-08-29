@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo Object Tracking - Windows Setup
echo ==========================================
echo.

set "PYEXE="

rem 1) Prefer Python Launcher if available.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.13 -c "import sys" >nul 2>nul
    if %errorlevel%==0 set "PYEXE=py -3.13"
)

rem 2) Try normal python command, but reject Microsoft Store alias failures.
if not defined PYEXE (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python -c "import sys" >nul 2>nul
        if %errorlevel%==0 set "PYEXE=python"
    )
)

rem 3) Check common Python 3.13 install locations.
if not defined PYEXE (
    if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
        set "PYEXE=%LocalAppData%\Programs\Python\Python313\python.exe"
    )
)
if not defined PYEXE (
    if exist "%ProgramFiles%\Python313\python.exe" (
        set "PYEXE=%ProgramFiles%\Python313\python.exe"
    )
)

rem 4) If Python is missing, install Python 3.13 with winget.
if not defined PYEXE (
    echo [INFO] Python 3.13 was not found.
    echo [INFO] Attempting automatic installation with Windows Package Manager...
    echo.

    where winget >nul 2>nul
    if errorlevel 1 goto no_winget

    winget install -e --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto install_python_fail

    rem Refresh common paths without requiring the terminal to restart.
    if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
        set "PYEXE=%LocalAppData%\Programs\Python\Python313\python.exe"
    )

    if not defined PYEXE (
        where py >nul 2>nul
        if %errorlevel%==0 (
            py -3.13 -c "import sys" >nul 2>nul
            if %errorlevel%==0 set "PYEXE=py -3.13"
        )
    )
)

if not defined PYEXE goto python_still_missing

echo [OK] Python:
%PYEXE% -c "import sys; print(sys.executable); print(sys.version)"
echo.

echo [1/3] Upgrading pip...
%PYEXE% -m pip install --upgrade pip
if errorlevel 1 goto fail

echo.
echo [2/3] Installing required packages...
%PYEXE% -m pip install -r requirements.txt
if errorlevel 1 goto fail

echo.
echo [3/3] Checking model and sample files...
if exist "detect.tflite" if exist "James.mp4" goto assets_ok

echo [INFO] Model/sample assets are missing. Downloading...
%PYEXE% download_assets.py
if errorlevel 1 goto fail

:assets_ok
echo.
echo ==========================================
echo Setup completed successfully.
echo ==========================================
echo.
echo Next:
echo   Double-click run_windows.bat
echo.
pause
exit /b 0

:no_winget
echo.
echo [ERROR] Python is not installed and winget is not available.
echo Install 64-bit Python 3.13 from:
echo   https://www.python.org/downloads/windows/
echo.
echo During setup, enable "Add python.exe to PATH".
pause
exit /b 1

:install_python_fail
echo.
echo [ERROR] Automatic Python installation failed.
echo Install 64-bit Python 3.13 manually from:
echo   https://www.python.org/downloads/windows/
echo.
echo Then run this file again.
pause
exit /b 1

:python_still_missing
echo.
echo [ERROR] Python installation completed but python.exe could not be located.
echo Close this window, open it again, and run install_windows.bat once more.
pause
exit /b 1

:fail
echo.
echo [ERROR] Setup failed.
echo Python used:
echo   %PYEXE%
echo.
pause
exit /b 1
