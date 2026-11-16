"""TFLiteSSD.detect()가 출력 텐서(boxes/classes/scores/num)를 바르게 구분하는지 가짜 인터프리터로 검사한다.

이름이 있는 출력(TFLite_Detection_PostProcess:N)은 이름으로, 이름이 없는 출력은 표준 순서와 값으로 구분한다.
이름 없이 [boxes, scores, classes, num] 순서인 모델도 점수와 클래스를 뒤바꾸지 않아야 한다.
"""
import numpy as np
import pytest

import object_tracking_pc as otp

POST = "TFLite_Detection_PostProcess"
BOXES = np.array([[0.1, 0.1, 0.9, 0.9]] + [[0.0, 0.0, 0.95, 0.95]] * 9, np.float32)
LABELS = ["???", "person", "bicycle", "car"]  # COCO_labels.txt처럼 0번은 배경, 클래스 번호 + 1로 찾는다


def tensors(scene):
    """scene: 'empty'(점수 모두 0), 'person'(0번 칸 사람 0.9), 'car'(0번 칸 자동차 0.8)."""
    classes = np.zeros(10, np.float32)
    scores = np.zeros(10, np.float32)
    if scene == "person":
        scores[0] = 0.9
    elif scene == "car":
        classes[:] = 2.0
        scores[0] = 0.8
    return {"boxes": BOXES, "classes": classes, "scores": scores, "num": np.array([10.0], np.float32)}


class FakeInterpreter:
    def __init__(self, order, names, scene):
        self.order, self.names, self.scene = order, names, scene

    def get_output_details(self):
        return [{"index": i, "name": n} for i, n in enumerate(self.names)]

    def set_tensor(self, *a):
        pass

    def invoke(self):
        pass

    def get_tensor(self, index):
        return tensors(self.scene)[self.order[index]]


def detector(order, names, scene):
    det = otp.TFLiteSSD.__new__(otp.TFLiteSSD)
    det.interpreter = FakeInterpreter(order, names, scene)
    det.labels = LABELS
    det.use_bgr_input = False
    det.output_details = det.interpreter.get_output_details()
    det.input_index, det.input_dtype, det.input_height, det.input_width = 0, np.uint8, 300, 300
    return det


STANDARD = ["boxes", "classes", "scores", "num"]
SCORES_FIRST = ["boxes", "scores", "classes", "num"]
NAMED = {"boxes": POST, "classes": f"{POST}:1", "scores": f"{POST}:2", "num": f"{POST}:3"}
CASES = [
    ("이름 있음·표준", STANDARD, [NAMED[k] for k in STANDARD]),
    ("이름 있음·섞임", ["scores", "num", "boxes", "classes"], [NAMED[k] for k in ["scores", "num", "boxes", "classes"]]),
    ("이름 없음·표준", STANDARD, [f"StatefulPartitionedCall:{i}" for i in range(4)]),
    ("이름 없음·점수 먼저", SCORES_FIRST, [f"StatefulPartitionedCall:{i}" for i in range(4)]),
]


@pytest.mark.parametrize("label,order,names", CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("scene,expected", [("empty", []), ("person", [("person", 0.9)]), ("car", [("car", 0.8)])])
def test_detect_maps_outputs(label, order, names, scene, expected):
    frame = np.zeros((480, 640, 3), np.uint8)
    found = detector(order, names, scene).detect(frame, threshold=0.45)
    assert [(d["label"], round(d["score"], 2)) for d in found] == expected
