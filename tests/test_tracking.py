"""검출·추적·메인 루프 테스트 (GUI 없이). detect.tflite·James.mp4가 필요하다."""
import hashlib
import sys
import threading

import cv2
import pytest
from conftest import LABELS, MODEL, SAMPLE_VIDEO, requires_assets

import object_tracking_pc as otp

# James.mp4 앞 30프레임의 검출 결과(라벨·점수·박스) SHA-256. 모델·후처리·라벨 대응이 바뀌면 달라진다.
EXPECTED_DETECTION_SHA256_PREFIX = "7e12946ad8f8"


@requires_assets
def test_detection_results_match_reference():
    detector = otp.TFLiteSSD(str(MODEL), str(LABELS))
    tracker = otp.MultiObjectTracker()
    capture = cv2.VideoCapture(str(SAMPLE_VIDEO))
    digest, labels = hashlib.sha256(), set()
    for n in range(30):
        ok, frame = capture.read()
        assert ok
        detections = detector.detect(frame)
        tracker.update(detections)
        for d in detections:
            labels.add(d["label"])
            digest.update(f"{n}:{d['label']}:{d['score']:.4f}:{[round(v, 1) for v in d['bbox']]}".encode())
    assert "person" in labels
    assert digest.hexdigest().startswith(EXPECTED_DETECTION_SHA256_PREFIX)


def test_tracker_keeps_id_for_moving_box():
    tracker = otp.MultiObjectTracker()
    ids = []
    for x in range(0, 50, 10):
        tracks = tracker.update([{"bbox": (x, 0, x + 40, 40), "class_id": 0, "label": "person", "score": 0.9}])
        ids.append([t.id for t in tracks if t.missed == 0])
    assert ids == [[1]] * 5


def _run_main(monkeypatch, video, wait_key, capture_cls=None, timeout=10):
    monkeypatch.setattr(otp.cv2, "imshow", lambda *a, **k: None)
    monkeypatch.setattr(otp.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(otp.cv2, "waitKey", wait_key)
    if capture_cls is not None:
        monkeypatch.setattr(otp.cv2, "VideoCapture", capture_cls)
    monkeypatch.setattr(sys, "argv", ["object_tracking_pc.py", "--video", str(video),
                                      "--model", str(MODEL), "--labels", str(LABELS)])
    done = threading.Event()
    errors = []

    def target():
        try:
            otp.main()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        done.set()

    threading.Thread(target=target, daemon=True).start()
    finished = done.wait(timeout)
    return finished, errors


@requires_assets
def test_unreadable_video_exits_instead_of_spinning(monkeypatch):
    reads = {"n": 0}

    class BrokenCapture:
        def __init__(self, *args, **kwargs):
            pass

        def isOpened(self):
            return True

        def read(self):
            reads["n"] += 1
            return False, None

        def set(self, *args):
            return True

        def release(self):
            pass

    finished, errors = _run_main(monkeypatch, "broken.mp4", lambda _: -1, BrokenCapture)
    assert finished, "읽을 수 없는 동영상에서 main()이 끝나지 않음(무한 반복)"
    assert errors == [] and reads["n"] <= 5


@requires_assets
def test_short_video_loops(monkeypatch, tmp_path):
    video = tmp_path / "short5.mp4"
    source = cv2.VideoCapture(str(SAMPLE_VIDEO))
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 180))
    for _ in range(5):
        writer.write(cv2.resize(source.read()[1], (320, 180)))
    writer.release()
    if cv2.VideoCapture(str(video)).get(cv2.CAP_PROP_FRAME_COUNT) != 5:
        pytest.skip("이 OpenCV 빌드에서 mp4v 테스트 영상을 만들 수 없습니다")

    shown = {"n": 0}

    def wait_key(_):
        shown["n"] += 1
        return ord("q") if shown["n"] >= 12 else -1

    finished, errors = _run_main(monkeypatch, video, wait_key)
    assert finished and errors == []
    assert shown["n"] == 12  # 5프레임 영상을 처음으로 되감으며 12프레임까지 재생
