@echo off
setlocal
cd /d "%~dp0"

if not exist detect.tflite (
    echo detect.tflite is missing. Running asset downloader...
    python download_assets.py
    if errorlevel 1 goto end
)

python object_tracking_pc.py --camera 0

:end
pause
