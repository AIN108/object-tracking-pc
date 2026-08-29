#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

python object_tracking_pc.py --camera 0 --width 640 --height 480 "$@"
