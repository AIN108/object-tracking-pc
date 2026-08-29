#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
USB Camera Object Detection + Tracking
--------------------------------------
Runs on Windows PC and Raspberry Pi with an OpenCV-compatible USB/V4L2 camera.

Model: TensorFlow Lite SSD MobileNet (detect.tflite)
Labels: COCO_labels.txt

Features:
- USB webcam or video-file input
- Bounding boxes
- Class name + confidence
- Persistent object ID
- Motion trail
- Track/object/FPS overlay
- Lightweight IoU + center-distance multi-object association

Raspberry Pi-specific GPIO, wiringPi, Unix socket, and ALLBASE dependencies
are intentionally not required in this standalone tracking version.
"""

import argparse
import math
import os
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np


def load_interpreter(model_path: str):
    errors = []

    # New LiteRT package, if available.
    try:
        from ai_edge_litert.interpreter import Interpreter
        interpreter = Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        return interpreter, "ai-edge-litert"
    except Exception as e:
        errors.append(f"ai-edge-litert: {e}")

    # Common lightweight Raspberry/Linux runtime.
    try:
        from tflite_runtime.interpreter import Interpreter
        interpreter = Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        return interpreter, "tflite-runtime"
    except Exception as e:
        errors.append(f"tflite-runtime: {e}")

    # Easiest general PC fallback.
    try:
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        return interpreter, "tensorflow"
    except Exception as e:
        errors.append(f"tensorflow: {e}")

    raise RuntimeError(
        "TensorFlow Lite interpreter를 불러올 수 없습니다.\n"
        "현재 Python 환경에 LiteRT를 설치하세요:\n"
        "  python -m pip install ai-edge-litert\n\n"
        "설치한 Python과 실행 중인 Python이 같은지도 확인하세요.\n\n"
        + "\n".join(errors)
    )


def load_labels(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def box_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter

    return inter / union if union > 0 else 0.0


def center_of(box):
    x1, y1, x2, y2 = box
    return ((x1 + x2) * 0.5, (y1 + y2) * 0.5)


def center_distance(a, b):
    ax, ay = center_of(a)
    bx, by = center_of(b)
    return math.hypot(ax - bx, ay - by)


class Track:
    def __init__(self, track_id, class_id, label, bbox, score, trail_len):
        self.id = track_id
        self.class_id = class_id
        self.label = label
        self.bbox = bbox
        self.score = score
        self.missed = 0
        self.hits = 1
        self.history = deque(maxlen=trail_len)
        self.history.append(tuple(map(int, center_of(bbox))))

    def update(self, bbox, score):
        self.bbox = bbox
        self.score = score
        self.missed = 0
        self.hits += 1
        self.history.append(tuple(map(int, center_of(bbox))))

    def mark_missed(self):
        self.missed += 1


class MultiObjectTracker:
    """
    Lightweight tracker for a PC/RPi demo.

    Association:
      1) same class only
      2) prefer IoU overlap
      3) allow center-distance matching when motion is moderate

    This is intentionally dependency-light and is not a Re-ID tracker such as
    DeepSORT/ByteTrack. IDs can change after long occlusion or severe overlap.
    """

    def __init__(
        self,
        max_missed=10,
        min_iou=0.12,
        max_center_distance=140.0,
        trail_len=32,
    ):
        self.max_missed = max_missed
        self.min_iou = min_iou
        self.max_center_distance = max_center_distance
        self.trail_len = trail_len
        self.next_id = 1
        self.tracks = []

    def _match_score(self, track, det):
        if track.class_id != det["class_id"]:
            return None

        iou = box_iou(track.bbox, det["bbox"])
        dist = center_distance(track.bbox, det["bbox"])

        # Valid if boxes overlap enough OR their centers remain reasonably close.
        if iou < self.min_iou and dist > self.max_center_distance:
            return None

        # Higher is better. IoU dominates; distance helps when objects move quickly.
        distance_score = max(0.0, 1.0 - dist / self.max_center_distance)
        return iou * 0.75 + distance_score * 0.25

    def update(self, detections):
        candidates = []
        for ti, tr in enumerate(self.tracks):
            for di, det in enumerate(detections):
                score = self._match_score(tr, det)
                if score is not None:
                    candidates.append((score, ti, di))

        candidates.sort(key=lambda x: x[0], reverse=True)

        used_tracks = set()
        used_dets = set()

        for _, ti, di in candidates:
            if ti in used_tracks or di in used_dets:
                continue
            tr = self.tracks[ti]
            det = detections[di]
            tr.update(det["bbox"], det["score"])
            used_tracks.add(ti)
            used_dets.add(di)

        # Existing tracks not associated this frame.
        for ti, tr in enumerate(self.tracks):
            if ti not in used_tracks:
                tr.mark_missed()

        # New detections become new tracks.
        for di, det in enumerate(detections):
            if di in used_dets:
                continue
            self.tracks.append(
                Track(
                    self.next_id,
                    det["class_id"],
                    det["label"],
                    det["bbox"],
                    det["score"],
                    self.trail_len,
                )
            )
            self.next_id += 1

        self.tracks = [t for t in self.tracks if t.missed <= self.max_missed]

        return self.tracks


class TFLiteSSD:
    def __init__(self, model_path, labels_path, use_bgr_input=False):
        self.interpreter, self.backend = load_interpreter(model_path)
        self.labels = load_labels(labels_path)
        self.use_bgr_input = use_bgr_input

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        if not self.input_details:
            raise RuntimeError("모델 input tensor를 찾지 못했습니다.")

        inp = self.input_details[0]
        shape = inp["shape"]
        if len(shape) != 4:
            raise RuntimeError(f"지원하지 않는 input tensor shape: {shape}")

        self.input_index = inp["index"]
        self.input_dtype = inp["dtype"]
        self.input_height = int(shape[1])
        self.input_width = int(shape[2])

    def _prepare_input(self, frame):
        resized = cv2.resize(frame, (self.input_width, self.input_height))

        if not self.use_bgr_input:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        x = np.expand_dims(resized, axis=0)

        if self.input_dtype == np.float32:
            x = x.astype(np.float32)
            x = (x - 127.5) / 127.5
        else:
            x = x.astype(self.input_dtype)

        return x

    @staticmethod
    def _squeeze_output(arr):
        arr = np.asarray(arr)
        return np.squeeze(arr)

    def detect(self, frame, threshold=0.45, person_only=False):
        h, w = frame.shape[:2]
        inp = self._prepare_input(frame)
        self.interpreter.set_tensor(self.input_index, inp)
        self.interpreter.invoke()

        outs = [
            self._squeeze_output(self.interpreter.get_tensor(info["index"]))
            for info in self.output_details
        ]

        boxes = classes = scores = num = None

        for arr in outs:
            a = np.asarray(arr)
            if a.ndim == 2 and a.shape[-1] == 4:
                boxes = a
            elif a.ndim == 1 and a.size > 1:
                if np.all((a >= -0.001) & (a <= 1.001)) and not np.allclose(a, np.round(a)):
                    if scores is None:
                        scores = a
                else:
                    if classes is None:
                        classes = a
            elif a.ndim == 0 or a.size == 1:
                try:
                    num = int(float(a.reshape(-1)[0]))
                except Exception:
                    pass

        if boxes is None and len(outs) >= 1:
            boxes = np.asarray(outs[0]).reshape(-1, 4)
        if classes is None and len(outs) >= 2:
            classes = np.asarray(outs[1]).reshape(-1)
        if scores is None and len(outs) >= 3:
            scores = np.asarray(outs[2]).reshape(-1)
        if num is None:
            if len(outs) >= 4:
                try:
                    num = int(float(np.asarray(outs[3]).reshape(-1)[0]))
                except Exception:
                    num = min(len(boxes), len(classes), len(scores))
            else:
                num = min(len(boxes), len(classes), len(scores))

        limit = min(num, len(boxes), len(classes), len(scores))
        detections = []

        for i in range(limit):
            score = float(scores[i])
            if score < threshold:
                continue

            raw_class = int(classes[i])
            label_index = raw_class + 1

            if 0 <= label_index < len(self.labels):
                label = self.labels[label_index]
            else:
                label = f"class_{raw_class}"

            if person_only and label.lower() != "person":
                continue

            y1, x1, y2, x2 = map(float, boxes[i])

            x1 = clamp(x1 * w, 0, w - 1)
            y1 = clamp(y1 * h, 0, h - 1)
            x2 = clamp(x2 * w, 0, w - 1)
            y2 = clamp(y2 * h, 0, h - 1)

            if x2 <= x1 or y2 <= y1:
                continue

            detections.append({
                "bbox": (x1, y1, x2, y2),
                "class_id": raw_class,
                "label": label,
                "score": score,
            })

        return detections


def color_for_id(track_id):
    hue = (track_id * 47) % 180
    hsv = np.uint8([[[hue, 210, 245]]])
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return tuple(int(v) for v in bgr)


def draw_track(frame, track):
    if track.missed > 2:
        return

    x1, y1, x2, y2 = map(int, track.bbox)
    color = color_for_id(track.id)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

    label = f"#{track.id} {track.label} {track.score * 100:.0f}%"
    (tw, th), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2
    )
    top = max(0, y1 - th - baseline - 8)
    right = min(frame.shape[1] - 1, x1 + tw + 10)

    cv2.rectangle(frame, (x1, top), (right, y1), color, -1)
    cv2.putText(
        frame,
        label,
        (x1 + 5, max(th + 2, y1 - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    pts = list(track.history)
    for i in range(1, len(pts)):
        thickness = max(1, int(3 * i / max(1, len(pts))))
        cv2.line(frame, pts[i - 1], pts[i], color, thickness, cv2.LINE_AA)

    if pts:
        cv2.circle(frame, pts[-1], 4, color, -1, cv2.LINE_AA)


def open_capture(camera_index, video_path, width, height):
    if video_path:
        cap = cv2.VideoCapture(video_path)
        source_name = video_path
    else:
        if os.name == "nt":
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(camera_index)
        else:
            cap = cv2.VideoCapture(camera_index)

        source_name = f"USB camera {camera_index}"
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        raise RuntimeError(f"영상 입력을 열 수 없습니다: {source_name}")

    return cap, source_name


BASE_DIR = Path(__file__).resolve().parent


def parse_args():
    p = argparse.ArgumentParser(
        description="TensorFlow Lite SSD + lightweight multi-object tracking"
    )
    p.add_argument("--model", default=str(BASE_DIR / "detect.tflite"))
    p.add_argument("--labels", default=str(BASE_DIR / "COCO_labels.txt"))
    p.add_argument("--camera", type=int, default=0, help="USB camera index (default: 0)")
    p.add_argument("--video", default=None, help="video file instead of USB camera")
    p.add_argument("--threshold", type=float, default=0.45)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--person-only", action="store_true")
    p.add_argument(
        "--bgr-input",
        action="store_true",
        help="Use old sample's BGR input instead of standard RGB",
    )
    p.add_argument("--max-missed", type=int, default=10)
    p.add_argument("--trail", type=int, default=32)
    return p.parse_args()


def main():
    args = parse_args()
    args.threshold = clamp(args.threshold, 0.01, 0.99)

    if not Path(args.model).exists():
        raise FileNotFoundError(
            f"모델 파일이 없습니다: {args.model}\n"
            "저장소 폴더에서 `python download_assets.py`를 먼저 실행하세요."
        )
    if not Path(args.labels).exists():
        raise FileNotFoundError(f"라벨 파일이 없습니다: {args.labels}")

    detector = TFLiteSSD(
        args.model,
        args.labels,
        use_bgr_input=args.bgr_input,
    )

    tracker = MultiObjectTracker(
        max_missed=max(1, args.max_missed),
        trail_len=max(2, args.trail),
    )

    cap, source_name = open_capture(
        args.camera,
        args.video,
        args.width,
        args.height,
    )

    print(f"TFLite backend : {detector.backend}")
    print(f"Input tensor   : {detector.input_width}x{detector.input_height} {detector.input_dtype}")
    print(f"Source         : {source_name}")
    print("종료: Q 또는 ESC")

    prev_time = time.perf_counter()
    fps_ema = 0.0

    try:
        while True:
            ok, frame = cap.read()

            if not ok or frame is None:
                if args.video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                print("카메라 프레임을 읽지 못했습니다.")
                break

            detections = detector.detect(
                frame,
                threshold=args.threshold,
                person_only=args.person_only,
            )
            tracks = tracker.update(detections)

            for tr in tracks:
                draw_track(frame, tr)

            now = time.perf_counter()
            instant_fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now
            fps_ema = instant_fps if fps_ema == 0 else fps_ema * 0.90 + instant_fps * 0.10

            visible_tracks = sum(1 for t in tracks if t.missed <= 2)
            visible_people = sum(
                1 for t in tracks if t.missed <= 2 and t.label.lower() == "person"
            )

            status = (
                f"TRACKS {visible_tracks}   "
                f"PEOPLE {visible_people}   "
                f"FPS {fps_ema:.1f}"
            )

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 42), (20, 20, 20), -1)
            cv2.putText(
                frame,
                status,
                (12, 29),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                (245, 245, 245),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Object Tracking - USB Camera", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
