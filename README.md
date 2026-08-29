# Object Tracking PC / Raspberry Pi

TensorFlow Lite SSD MobileNet으로 카메라 영상의 객체를 검출하고, 프레임 사이의 검출 결과를 연결해 **Bounding Box, 클래스명, confidence, 객체 ID, 이동 궤적**을 표시하는 경량 Object Tracking 프로젝트입니다.

PC의 USB 웹캠과 Raspberry Pi의 USB 웹캠에서 같은 Python 코드를 사용할 수 있습니다.

> Raspberry Pi의 CSI Camera Module(Pi Camera)은 이 기본판의 직접 입력 대상이 아닙니다. 이 저장소의 기본 입력은 `OpenCV VideoCapture`가 열 수 있는 USB/V4L2 카메라입니다. Pi Camera를 쓰려면 Picamera2 입력 어댑터가 별도로 필요합니다.

## 주요 기능

- USB 웹캠 실시간 입력
- 동영상 파일 입력
- TensorFlow Lite SSD MobileNet 객체 검출
- COCO 클래스명 표시
- Bounding Box 표시
- confidence 표시
- 객체별 Tracking ID
- 객체 이동 궤적
- 여러 객체 동시 추적
- 현재 Tracking 객체 수 / Person 수 / FPS 표시
- `--person-only` 사람 전용 추적
- `--threshold` confidence 기준 조정
- 테스트 동영상 반복 재생

## 동작 구조

```text
USB Camera / Video
        ↓
TensorFlow Lite SSD MobileNet
        ↓
Object Detection
        ↓
Bounding Box + Class + Confidence
        ↓
IoU + Center Distance Association
        ↓
Object ID
        ↓
Motion Trail
        ↓
OpenCV Display
```

현재 tracker는 별도의 DeepSORT/ByteTrack 의존성을 추가하지 않은 **IoU + 중심점 거리 기반 경량 추적기**입니다. 사람이 서로 심하게 겹치거나 오랫동안 화면에서 사라졌다가 다시 나타나면 ID가 바뀔 수 있습니다.

---

# 빠른 시작

저장소를 받은 뒤 먼저 모델 파일과 샘플 영상을 준비합니다.

```bash
python download_assets.py
```

이 명령은 원본 Qengineering 프로젝트에서 다음 파일을 내려받습니다.

- `detect.tflite`
- `James.mp4`

`COCO_labels.txt`는 저장소에 포함되어 있습니다.

---

# 1. 새 Windows PC에서 실행

## 준비물

- Windows 10 또는 Windows 11
- 64-bit Python 3.10 ~ 3.13 권장
- USB 웹캠

LiteRT 2.2.0은 Windows x86-64용 Python 3.10~3.14 wheel이 제공됩니다.

## 저장소 받기

Git이 설치되어 있다면:

```powershell
git clone https://github.com/AIN108/object-tracking-pc.git
cd object-tracking-pc
```

또는 GitHub에서 ZIP으로 내려받아 압축을 풀어도 됩니다.

## 가상환경 만들기

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 때문에 활성화가 막히면, 가상환경을 사용하지 않고 같은 Python 실행 파일로 `-m pip`와 프로그램을 직접 실행해도 됩니다.

## 패키지 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

또는:

```text
install_windows.bat
```

## 모델과 샘플 영상 받기

```powershell
python download_assets.py
```

## 샘플 영상으로 먼저 확인

```powershell
python object_tracking_pc.py --video James.mp4
```

정상이라면 영상 위에 객체 박스와 다음 정보가 표시됩니다.

```text
#1 person 94%
#2 car 87%
TRACKS 2   PEOPLE 1   FPS 20.4
```

## USB 웹캠 실행

```powershell
python object_tracking_pc.py
```

기본 카메라는 `0`번입니다.

카메라가 여러 개라면:

```powershell
python object_tracking_pc.py --camera 1
```

또는:

```powershell
python object_tracking_pc.py --camera 2
```

## Windows에서 Python이 여러 개 설치된 경우

어느 Python을 실행하는지 먼저 확인합니다.

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

특정 Python을 직접 지정할 수도 있습니다.

```powershell
& "C:\Path\To\Python313\python.exe" -m pip install -r requirements.txt
& "C:\Path\To\Python313\python.exe" download_assets.py
& "C:\Path\To\Python313\python.exe" object_tracking_pc.py
```

LiteRT 확인:

```powershell
python -c "from ai_edge_litert.interpreter import Interpreter; print('LiteRT OK')"
```

`LiteRT OK`가 나오면 interpreter 설치는 정상입니다.

---

# 2. 새 Raspberry Pi에서 실행

## 권장 환경

- Raspberry Pi 4 또는 Raspberry Pi 5
- 64-bit Raspberry Pi OS 권장
- Raspberry Pi OS Desktop 또는 GUI를 사용할 수 있는 환경
- USB 웹캠

현재 LiteRT 2.2.0에는 Linux ARM64(aarch64)용 wheel이 제공되므로 64-bit Raspberry Pi OS에서 설치하기가 가장 편합니다.

## 저장소 받기

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip python3-opencv v4l-utils
git clone https://github.com/AIN108/object-tracking-pc.git
cd object-tracking-pc
```

## USB 카메라 확인

카메라를 연결한 뒤:

```bash
v4l2-ctl --list-devices
```

또는:

```bash
ls /dev/video*
```

보통 첫 USB 웹캠은 `/dev/video0`이며 프로그램에서는 `--camera 0`에 해당합니다.

## Raspberry Pi용 가상환경

Raspberry Pi OS의 `python3-opencv`를 그대로 사용하기 위해 system site packages를 포함한 venv를 권장합니다.

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

## LiteRT 설치

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements_raspberry.txt
```

또는:

```bash
chmod +x setup_raspberry.sh
./setup_raspberry.sh
```

LiteRT 확인:

```bash
python -c "from ai_edge_litert.interpreter import Interpreter; print('LiteRT OK')"
```

## 모델과 샘플 영상 받기

```bash
python download_assets.py
```

## 샘플 영상 테스트

카메라보다 먼저 추론이 정상인지 확인하려면:

```bash
python object_tracking_pc.py --video James.mp4
```

## USB 웹캠 실행

```bash
python object_tracking_pc.py --camera 0
```

Raspberry Pi에서는 처리 부하를 줄이기 위해 먼저 640×480을 권장합니다.

```bash
python object_tracking_pc.py --camera 0 --width 640 --height 480
```

사람만 추적하면 객체 수가 줄어 조금 더 단순하게 확인할 수 있습니다.

```bash
python object_tracking_pc.py --camera 0 --width 640 --height 480 --person-only
```

다른 USB 카메라라면:

```bash
python object_tracking_pc.py --camera 1 --width 640 --height 480
```

## Raspberry Pi에서 화면이 뜨지 않을 때

이 프로그램은 `cv2.imshow()`로 결과 창을 표시하므로 **그래픽 데스크톱 세션**이 필요합니다.

SSH만 접속한 완전한 headless 환경에서는 창이 열리지 않습니다. 그 경우에는 별도의 headless 출력/웹 스트리밍 버전이 필요합니다.

## Pi Camera Module을 쓰고 싶은 경우

현재 기본판은 USB/V4L2 카메라를 대상으로 합니다.

Raspberry Pi Camera Module 2/3 등의 CSI 카메라는 최신 Raspberry Pi OS에서 Picamera2/libcamera 계열을 사용하는 것이 일반적이며, 이 프로젝트에 연결하려면 프레임 입력부를 Picamera2용으로 바꿔야 합니다.

즉:

```text
USB Webcam
    → 현재 코드 그대로 사용 가능

Pi Camera Module
    → Picamera2 입력 버전 필요
```

---

# 3. 공통 실행 옵션

## 사람만 추적

```bash
python object_tracking_pc.py --person-only
```

## confidence 기준 낮추기

기본값은 `0.45`입니다.

```bash
python object_tracking_pc.py --threshold 0.30
```

## 오검출 줄이기

```bash
python object_tracking_pc.py --threshold 0.55
```

## 이동 궤적 길이 변경

```bash
python object_tracking_pc.py --trail 50
```

## 객체가 잠깐 사라졌을 때 ID 유지 시간 변경

```bash
python object_tracking_pc.py --max-missed 15
```

## 기존 Qengineering C++ 예제와 같은 BGR 입력 비교

기본값은 RGB 입력입니다.

```bash
python object_tracking_pc.py --bgr-input
```

## 종료

- `Q`
- `ESC`

---

# 프로젝트 구성

```text
object-tracking-pc/
├─ object_tracking_pc.py
├─ download_assets.py
├─ COCO_labels.txt
├─ requirements.txt
├─ requirements_raspberry.txt
├─ install_windows.bat
├─ run_windows.bat
├─ setup_raspberry.sh
├─ run_raspberry.sh
├─ .gitignore
├─ LICENSE
└─ README.md

실행 전에 download_assets.py로 생성:
├─ detect.tflite
└─ James.mp4
```

---

# 문제 해결

## `No module named 'cv2'`

현재 실행 중인 Python 환경에 OpenCV가 없습니다.

Windows:

```powershell
python -m pip install opencv-python
```

Raspberry Pi:

```bash
sudo apt install python3-opencv
```

venv를 사용한다면 `--system-site-packages`로 생성했는지 확인합니다.

## `No module named 'ai_edge_litert'`

```bash
python -m pip install ai-edge-litert
```

설치한 Python과 실행하는 Python이 같은지 확인합니다.

## NumPy 1.x / 2.x 관련 TensorFlow 오류

이 프로젝트는 전체 TensorFlow가 없어도 됩니다. 기본적으로 `ai-edge-litert`를 사용합니다.

PC에 여러 Python/TensorFlow 환경이 섞여 있다면:

```bash
python -c "import sys; print(sys.executable)"
```

로 현재 interpreter를 확인하고, 같은 Python에서 LiteRT를 설치하고 프로그램을 실행하십시오.

## 카메라가 열리지 않음

Windows:

```powershell
python object_tracking_pc.py --camera 1
```

처럼 번호를 바꿔 확인합니다.

Raspberry Pi:

```bash
v4l2-ctl --list-devices
```

로 실제 USB 카메라 번호를 확인합니다.

---

# 원본 및 출처

TensorFlow Lite SSD 모델과 기본 C++ 예제 구성은 다음 프로젝트를 기반으로 합니다.

**Qengineering / TensorFlow_Lite_SSD_RPi_64-bits**

https://github.com/Qengineering/TensorFlow_Lite_SSD_RPi_64-bits

원본 프로젝트는 **BSD 3-Clause License**입니다.

이 저장소에서는 PC/Raspberry Pi USB 카메라에서 쉽게 시험할 수 있도록 다음 요소를 추가하거나 재구성했습니다.

- Python 기반 실행판
- USB 웹캠 입력
- Windows 실행 지원
- Raspberry Pi USB 카메라 실행 절차
- IoU + 중심점 거리 기반 Multi-object association
- Object ID
- Motion trail
- Tracking/Person/FPS overlay
- 다운로드 스크립트 및 설치 스크립트

# License

BSD 3-Clause License. 자세한 내용은 `LICENSE`를 참고하십시오.
