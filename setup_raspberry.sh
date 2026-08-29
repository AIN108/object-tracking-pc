#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv v4l-utils

if [ ! -d ".venv" ]; then
  python3 -m venv --system-site-packages .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements_raspberry.txt

if [ ! -f "detect.tflite" ] || [ ! -f "James.mp4" ]; then
  echo
  echo "[INFO] Model/sample assets are missing."
  echo "[INFO] Downloading them now..."
  python download_assets.py
fi

echo
echo "Setup complete."
echo "Run:"
echo "  source .venv/bin/activate"
echo "  python object_tracking_pc.py --camera 0 --width 640 --height 480"
