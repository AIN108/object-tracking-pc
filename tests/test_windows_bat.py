"""install_windows.bat / run_windows.bat의 Python 선택 로직 검증 (Windows 전용).

배치 파일을 임시 폴더에 복사하고 PATH를 통제해 다음 상황을 만든다.
- "py 런처는 있지만 3.13이 없음": 가짜 py.exe(where.exe 복사본)는 `py -3.13 ...`에 0이 아닌 코드를 낸다.
- "Microsoft Store 별칭만 있음": 가짜 python.exe(where.exe 복사본)는 `python -c ...`에 0이 아닌 코드를 낸다.
- "실제 Python": 테스트를 실행 중인 Python 폴더를 PATH에 넣는다.
object_tracking_pc.py는 실행 Python을 출력만 하는 가짜로 바꾸고, requirements.txt는 비워 둔다.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import ROOT

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows cmd.exe에서만 실행")

SYSTEM32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
WHERE_EXE = SYSTEM32 / "where.exe"


def _workspace(tmp_path, py_missing_313=False, store_alias_python=False, real_python=False):
    work = tmp_path / "app"
    work.mkdir()
    for name in ("install_windows.bat", "run_windows.bat"):
        shutil.copy(ROOT / name, work / name)
    (work / "requirements.txt").write_text("", encoding="ascii")
    (work / "detect.tflite").write_bytes(b"dummy")
    (work / "James.mp4").write_bytes(b"dummy")
    (work / "download_assets.py").write_text("print('download skipped')\n", encoding="ascii")
    (work / "object_tracking_pc.py").write_text(
        "import sys\nprint('RAN-WITH-PYTHON', sys.executable)\n", encoding="ascii")

    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    if py_missing_313:
        shutil.copy(WHERE_EXE, fakebin / "py.exe")
    if store_alias_python:
        shutil.copy(WHERE_EXE, fakebin / "python.exe")

    path = [str(fakebin)]
    if real_python:
        path.append(str(Path(sys.executable).parent))
    path.append(str(SYSTEM32))
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(path)
    # 기본 설치 경로(%LocalAppData%\...\Python313, %ProgramFiles%\Python313)에 실제 Python이 잡히지 않게 한다
    # (Windows의 os.environ 키는 대문자이므로 대문자로 덮어쓴다)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["PROGRAMFILES"] = str(tmp_path / "programfiles")
    return work, env


def _run(work, env, script):
    result = subprocess.run(["cmd", "/c", script], cwd=work, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=900)
    return result.returncode, result.stdout + result.stderr


def test_run_skips_py_launcher_without_313(tmp_path):
    work, env = _workspace(tmp_path, py_missing_313=True, real_python=True)
    code, out = _run(work, env, "run_windows.bat")
    assert "RAN-WITH-PYTHON" in out, out
    assert code == 0, out


def test_run_rejects_store_alias_python(tmp_path):
    work, env = _workspace(tmp_path, store_alias_python=True)
    code, out = _run(work, env, "run_windows.bat")
    assert "Python was not found" in out, out
    assert "RAN-WITH-PYTHON" not in out
    assert code == 1, out


def test_install_skips_py_launcher_without_313(tmp_path):
    work, env = _workspace(tmp_path, py_missing_313=True, real_python=True)
    code, out = _run(work, env, "install_windows.bat")
    assert "Setup completed successfully" in out, out
    assert str(Path(sys.executable).parent).lower() in out.lower(), out  # [OK] Python: 에 실제 Python 경로
    assert code == 0, out


def test_install_rejects_store_alias_python(tmp_path):
    work, env = _workspace(tmp_path, store_alias_python=True)
    code, out = _run(work, env, "install_windows.bat")
    # PATH에 winget이 없으므로 자동 설치 대신 안내 메시지로 끝나야 한다 (별칭을 Python으로 쓰지 않음)
    assert "winget is not available" in out, out
    assert "Setup failed" not in out
    assert code == 1, out
