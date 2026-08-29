# Object Tracking PC / Raspberry Pi

TensorFlow Lite SSD MobileNet으로 카메라 영상의 객체를 검출하고, 프레임 사이의 검출 결과를 연결해 **Bounding Box, 클래스명, Confidence, 객체 ID, 이동 궤적**을 표시하는 경량 Object Tracking 프로젝트입니다.

PC의 USB 웹캠과 Raspberry Pi의 USB 웹캠에서 같은 Python 코드를 사용할 수 있습니다.

## 배포 방식

이 프로젝트는 두 방식으로 사용할 수 있습니다.

### 1. 완전판 ZIP — 권장

`object-tracking-complete.zip`에는 다음 실행 자산까지 모두 포함됩니다.

```text
detect.tflite
COCO_labels.txt
James.mp4
```

따라서 ZIP을 받은 사용자는 **모델이나 샘플 영상을 별도로 내려받을 필요가 없습니다.**

### 2. GitHub 소스 clone

GitHub 저장소 자체는 소스 중심으로 관리합니다. `detect.tflite` 또는 `James.mp4`가 없는 상태에서 설치 스크립트를 실행하면 `download_assets.py`가 필요한 파일만 자동으로 받아옵니다.

즉 완전판 ZIP에서는 다운로드를 건너뛰고, GitHub clone에서는 누락 자산만 자동 복구합니다.

---

## 주요 기능

- USB 웹캠 실시간 입력
- 동영상 파일 입력
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

현재 tracker는 별도의 DeepSORT/ByteTrack 의존성을 추가하지 않은 **IoU + 중심점 거리 기반 경량 추적기**입니다. 객체가 서로 심하게 겹치거나 오랫동안 화면에서 사라졌다가 다시 나타나면 ID가 변경될 수 있습니다.

---

# Windows PC에서 실행

## 권장 환경

- Windows 10 / 11
- 64-bit Python 3.10 ~ 3.13 권장
- USB 웹캠

## 완전판 ZIP 사용

ZIP을 원하는 폴더에 압축 해제합니다.

```text
object-tracking-complete/
├─ object_tracking_pc.py
├─ detect.tflite
├─ COCO_labels.txt
├─ James.mp4
├─ requirements.txt
├─ requirements_raspberry.txt
├─ install_windows.bat
├─ run_windows.bat
├─ setup_raspberry.sh
├─ run_raspberry.sh
├─ download_assets.py
├─ LICENSE
└─ README.md
```

압축을 푼 뒤 가장 간단한 방법은 다음과 같습니다.

```text
1. install_windows.bat 실행
2. run_windows.bat 실행
```

`install_windows.bat`은 모델과 샘플 영상이 이미 있으면 다시 다운로드하지 않습니다.

## GitHub에서 받기

```powershell
git clone https://github.com/AIN108/object-tracking-pc.git
cd object-tracking-pc
```

그 다음:

```text
install_windows.bat
```

을 실행하면 Python 패키지를 설치하고, 모델/샘플 영상이 없을 경우에만 자동 다운로드합니다.

직접 설치하려면:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

GitHub clone에서 자산이 없다면:

```powershell
python download_assets.py
```

를 수동으로 실행할 수도 있습니다.

## 샘플 영상으로 확인

```powershell
python object_tracking_pc.py --video James.mp4
```

정상이라면 다음과 같은 정보가 영상 위에 표시됩니다.

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

다른 카메라를 사용하려면:

```powershell
python object_tracking_pc.py --camera 1
```

또는:

```powershell
python object_tracking_pc.py --camera 2
```

## Python이 여러 버전 설치된 경우

현재 실행되는 Python을 확인합니다.

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

특정 Python을 직접 지정할 수도 있습니다.

```powershell
& "C:\Path\To\Python313\python.exe" -m pip install -r requirements.txt
& "C:\Path\To\Python313\python.exe" object_tracking_pc.py
```

LiteRT 확인:

```powershell
python -c "from ai_edge_litert.interpreter import Interpreter; print('LiteRT OK')"
```

---

# Raspberry Pi에서 실행

## 권장 환경

- Raspberry Pi 4 또는 Raspberry Pi 5
- 64-bit Raspberry Pi OS 권장
- Raspberry Pi OS Desktop 또는 GUI 환경
- USB 웹캠

이 기본판은 **USB 웹캠 / V4L2 입력** 기준입니다.

Raspberry Pi CSI Camera Module을 직접 사용하려면 Picamera2 입력 버전이 별도로 필요합니다.

## 완전판 ZIP 사용

ZIP을 USB 메모리, SCP, 네트워크 공유 등으로 Raspberry Pi에 복사한 뒤 압축을 풉니다.

```bash
unzip object-tracking-complete.zip
cd object-tracking-complete
```

기본 패키지 설치:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv v4l-utils
```

가상환경:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

LiteRT 설치:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements_raspberry.txt
```

또는 한 번에:

```bash
chmod +x setup_raspberry.sh
./setup_raspberry.sh
```

완전판 ZIP에는 모델과 샘플 영상이 이미 있으므로 `setup_raspberry.sh`는 해당 파일을 다시 받지 않습니다.

## GitHub에서 받기

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip python3-opencv v4l-utils
git clone https://github.com/AIN108/object-tracking-pc.git
cd object-tracking-pc
chmod +x setup_raspberry.sh run_raspberry.sh
./setup_raspberry.sh
```

GitHub clone에 모델/샘플 영상이 없으면 setup 스크립트가 자동으로 내려받습니다.

## USB 카메라 확인

```bash
v4l2-ctl --list-devices
```

또는:

```bash
ls /dev/video*
```

보통 첫 USB 웹캠은 `/dev/video0`이며 프로그램에서는 `--camera 0`에 해당합니다.

## 샘플 영상 테스트

```bash
python object_tracking_pc.py --video James.mp4
```

## USB 웹캠 실행

Raspberry Pi에서는 처리 부하를 줄이기 위해 640×480부터 시작하는 것을 권장합니다.

```bash
python object_tracking_pc.py --camera 0 --width 640 --height 480
```

실행 스크립트:

```bash
./run_raspberry.sh
```

다른 USB 카메라라면:

```bash
python object_tracking_pc.py --camera 1 --width 640 --height 480
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

로 실제 interpreter를 확인하고 같은 Python에서 LiteRT를 설치하고 실행하십시오.

## USB 카메라가 열리지 않음

카메라 번호를 바꿔 시험합니다.

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

현재 기본 프로그램은 `cv2.imshow()`를 사용하므로 GUI가 없는 Raspberry Pi OS Lite/headless 환경에서는 창을 직접 표시할 수 없습니다.

---

# 복구용 모델 다운로드

완전판 ZIP에서는 실행할 필요가 없습니다.

`detect.tflite` 또는 `James.mp4`가 삭제됐을 때만:

```bash
python download_assets.py
```

를 실행하면 됩니다.

---

# 원본 및 출처

TensorFlow Lite SSD 기본 예제와 모델 구성은 다음 프로젝트를 기반으로 합니다.

**Qengineering / TensorFlow_Lite_SSD_RPi_64-bits**

https://github.com/Qengineering/TensorFlow_Lite_SSD_RPi_64-bits

원본 프로젝트는 BSD 3-Clause License입니다.

본 프로젝트에서는 PC/Raspberry Pi USB 카메라 실행, 여러 객체 연결, Object ID, 이동 궤적, 상태 표시, 설치/복구 절차 등을 추가하거나 재구성했습니다.

# License

BSD 3-Clause License. 자세한 내용은 `LICENSE`를 참고하십시오.
