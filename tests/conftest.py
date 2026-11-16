import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL = ROOT / "detect.tflite"
LABELS = ROOT / "COCO_labels.txt"
SAMPLE_VIDEO = ROOT / "James.mp4"

requires_assets = pytest.mark.skipif(
    not (MODEL.exists() and SAMPLE_VIDEO.exists()),
    reason="detect.tflite / James.mp4가 없습니다. 먼저 `python download_assets.py`를 실행하세요.",
)
