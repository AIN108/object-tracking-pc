# Object Tracking PC / Raspberry Pi

TensorFlow Lite SSD MobileNet으로 카메라 영상의 객체를 검출하고, 프레임 사이의 검출 결과를 연결해 **Bounding Box, 클래스명, Confidence, 객체 ID, 이동 궤적**을 표시하는 경량 Object Tracking 프로젝트입니다.

PC의 USB 웹캠과 Raspberry Pi의 USB 웹캠에서 같은 Python 코드를 사용할 수 있습니다.

> **Windows 새 PC:** Python이 설치되어 있지 않아도 `install_windows.bat`를 실행하면 `winget`으로 Python 3.13 설치를 시도한 뒤 필요한 Python 패키지 설치까지 이어서 진행합니다.

## 배포 방식

### 1. 완전판 ZIP — 가장 간단한 배포용

`object-tracking-complete-v3.zip`에는 실행에 필요한 다음 자산까지 포함됩니다.

```text
detect.tflite
COCO_labels.txt
James.mp4
```

따라서 ZIP을 받은 사용자는 모델이나 샘플 영상을 따로 받을 필요가 없습니다.

Windows에서는 압축을 푼 뒤:

```text
1. install_windows.bat 실행
2. 설치 완료 후 run_windows.bat 실행
```

이면 됩니다.

### 2. GitHub clone

GitHub 저장소는 소스 중심으로 관리합니다. `detect.tflite` 또는 `James.mp4`가 없는 경우 설치/실행 스크립트가 `download_assets.py`를 이용해 누락된 자산을 자동으로 내려받습니다.

```powershell
git clone https://github.com/AIN108/object-tracking-pc.git
cd object-tracking-pc
```

---

## 주요 기능

- USB 웹캠 실시간 입력
- MP4 동영상 입력
- TensorFlow Lite SSD MobileNet 객체 검출
- COCO 클래스명 표시
- Bounding Box 표시
- Confidence 표시
- 객체별 Tracking ID
- 객체 이동 궤적
- 여러 객체 동시 추적
- 현재 Tracking 객체 수 / Person 수 / FPS 표시
- `--person-only` 사람 전용 추적
- `--threshold` Confidence 기준 조정
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

현재 tracker는 별도의 DeepSORT/ByteTrack 의존성을 추가하지 않은 **IoU + 중심점 거리 기반 경량 추적기**입니다. 객체가 서로 심하게 겹치거나 오래 사라졌다가 다시 나타나면 ID가 바뀔 수 있습니다.

---

# Windows PC에서 실행

## 권장 환경

- Windows 10 / 11
- 64-bit Python 3.13 권장
- USB 웹캠

## 새 PC에서 가장 간단한 방법

완전판 ZIP을 압축 해제하거나 GitHub 저장소를 clone한 뒤 `install_windows.bat`를 실행합니다.

```text
install_windows.bat
```

설치 스크립트는 다음 순서로 동작합니다.

1. Python Launcher의 Python 3.13 확인
2. 일반 `python` 명령 확인
3. 일반적인 Python 3.13 설치 경로 확인
4. Python이 없으면 `winget`으로 Python 3.13 자동 설치 시도
5. `pip` 업그레이드
6. `requirements.txt` 설치
7. `detect.tflite` / `James.mp4` 확인
8. 누락되어 있으면 `download_assets.py` 실행

설치가 끝나면:

```text
run_windows.bat
```

을 실행합니다.

`run_windows.bat`도 Python 3.13을 우선 찾아 실행하므로, Microsoft Store의 가짜 `python` 실행 별칭 때문에 잘못된 Python이 실행되는 문제를 줄였습니다.

## winget이 없는 경우

`install_windows.bat`에서 Python 자동 설치가 불가능하면 Python 3.13 64-bit를 직접 설치합니다.

https://www.python.org/downloads/windows/

설치 중 가능하면 **Add python.exe to PATH**를 활성화하고, 설치 후 `install_windows.bat`를 다시 실행합니다.

## 직접 설치

이미 사용할 Python이 있다면:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Python이 여러 버전 설치되어 있다면 설치와 실행에 같은 Python을 사용하십시오.

예:

```powershell
& "C:\Path\To\Python313\python.exe" -m pip install -r requirements.txt
& "C:\Path\To\Python313\python.exe" object_tracking_pc.py
```

## LiteRT 설치 확인

```powershell
python -c "from ai_edge_litert.interpreter import Interpreter; print('LiteRT OK')"
```

## 샘플 영상으로 먼저 확인

완전판 ZIP에는 `James.mp4`가 이미 포함되어 있습니다.

```powershell
python object_tracking_pc.py --video James.mp4
```

GitHub clone에서 영상이나 모델 파일이 없다면:

```powershell
python download_assets.py
```

으로 받을 수도 있습니다.

정상 실행 시 영상 위에 다음과 같은 정보가 표시됩니다.

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

다른 카메라:

```powershell
python object_tracking_pc.py --camera 1
```

```powershell
python object_tracking_pc.py --camera 2
```

## Python 환경 확인

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

---

# Raspberry Pi에서 실행

## 권장 환경

- Raspberry Pi 4 또는 Raspberry Pi 5
- 64-bit Raspberry Pi OS 권장
- Raspberry Pi OS Desktop 또는 GUI 환경
- USB 웹캠

이 기본판은 **USB 웹캠 / V4L2 입력** 기준입니다.

Raspberry Pi CSI Camera Module을 직접 사용하려면 Picamera2 입력 어댑터가 별도로 필요합니다.

## GitHub에서 받기

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip python3-opencv v4l-utils
git clone https://github.com/AIN108/object-tracking-pc.git
cd object-tracking-pc
```

## 완전판 ZIP 사용

ZIP 파일을 Raspberry Pi로 복사했다면:

```bash
unzip object-tracking-complete-v3.zip
cd object-tracking-complete-v3
```

완전판 ZIP에는 `detect.tflite`와 `James.mp4`가 이미 들어 있습니다.

## USB 카메라 확인

```bash
v4l2-ctl --list-devices
```

또는:

```bash
ls /dev/video*
```

보통 첫 USB 웹캠은 `/dev/video0`이며 프로그램에서는 `--camera 0`입니다.

## Raspberry Pi 설치

한 번에:

```bash
chmod +x setup_raspberry.sh run_raspberry.sh
./setup_raspberry.sh
```

직접 설치하려면:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv v4l-utils
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements_raspberry.txt
```

GitHub clone에서 모델/샘플 영상이 없다면 setup 스크립트가 자동으로 내려받습니다.

## 샘플 영상 테스트

```bash
python object_tracking_pc.py --video James.mp4
```

## USB 웹캠 실행

Raspberry Pi에서는 처리 부하를 줄이기 위해 640×480부터 시작하는 것을 권장합니다.

```bash
python object_tracking_pc.py --camera 0 --width 640 --height 480
```

또는:

```bash
./run_raspberry.sh
```

---

# 공통 옵션

사람만 추적:

```bash
python object_tracking_pc.py --person-only
```

Confidence 기준 낮추기:

```bash
python object_tracking_pc.py --threshold 0.30
```

오검출 줄이기:

```bash
python object_tracking_pc.py --threshold 0.55
```

카메라 해상도:

```bash
python object_tracking_pc.py --width 640 --height 480
```

이동 궤적 길이:

```bash
python object_tracking_pc.py --trail 48
```

객체가 잠시 사라졌을 때 ID 유지 프레임 수:

```bash
python object_tracking_pc.py --max-missed 15
```

종료:

- `Q`
- `ESC`

---

# 문제 해결

## `Python was not found... Microsoft Store`

이 메시지는 실제 Python 대신 Windows App Execution Alias가 실행된 경우가 많습니다.

최신 `install_windows.bat`는 이 별칭을 정상 Python으로 간주하지 않고 Python 3.13을 다시 찾거나 설치합니다.

따라서 먼저:

```text
install_windows.bat
```

을 다시 실행하십시오.

## `No module named 'cv2'`

Windows:

```powershell
python -m pip install opencv-python
```

Raspberry Pi:

```bash
sudo apt install python3-opencv
```

## `No module named 'ai_edge_litert'`

```bash
python -m pip install ai-edge-litert
```

설치한 Python과 실행하는 Python이 같은지 확인하십시오.

## NumPy / 구형 TensorFlow 충돌

이 프로젝트는 전체 TensorFlow가 없어도 됩니다. 기본적으로 `ai-edge-litert`를 사용합니다.

```bash
python -c "import sys; print(sys.executable)"
```

로 실제 interpreter를 확인하십시오.

## USB 카메라가 열리지 않음

카메라 번호를 변경합니다.

```bash
python object_tracking_pc.py --camera 1
```

```bash
python object_tracking_pc.py --camera 2
```

Raspberry Pi에서는:

```bash
v4l2-ctl --list-devices
```

로 실제 장치를 확인합니다.

## Raspberry Pi에서 결과 창이 열리지 않음

현재 기본 프로그램은 `cv2.imshow()`를 사용하므로 GUI가 없는 Raspberry Pi OS Lite/headless 환경에서는 결과 창을 직접 표시할 수 없습니다.

---

# 파일 구성

GitHub 소스 기준:

```text
object-tracking-pc/
├─ object_tracking_pc.py
├─ COCO_labels.txt
├─ download_assets.py
├─ requirements.txt
├─ requirements_raspberry.txt
├─ install_windows.bat
├─ run_windows.bat
├─ setup_raspberry.sh
├─ run_raspberry.sh
├─ LICENSE
└─ README.md
```

완전판 ZIP에는 여기에 다음 파일이 추가되어 있습니다.

```text
detect.tflite
James.mp4
```

---

# 원본 및 출처

TensorFlow Lite SSD 기본 예제와 모델 구성은 다음 프로젝트를 기반으로 합니다.

**Qengineering / TensorFlow_Lite_SSD_RPi_64-bits**

https://github.com/Qengineering/TensorFlow_Lite_SSD_RPi_64-bits

원본 프로젝트는 BSD 3-Clause License입니다.

본 프로젝트에서는 PC/Raspberry Pi USB 카메라 실행, 여러 객체 연결, Object ID, 이동 궤적, 상태 표시, Windows 자동 설치/복구 절차 등을 추가하거나 재구성했습니다.

# License

BSD 3-Clause License. 자세한 내용은 `LICENSE`를 참고하십시오.
