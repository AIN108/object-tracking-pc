"""download_assets.py: 로컬 HTTP 서버로 정상·끊김·재실행을 확인한다 (외부 네트워크 불필요)."""
import http.server
import importlib.util
import shutil
import threading

import pytest
from conftest import ROOT

PAYLOAD = b"M" * (3 * 1024 * 1024 + 123)


@pytest.fixture
def asset_server():
    state = {"broken": False}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            if state["broken"]:
                self.wfile.write(PAYLOAD[: 1024 * 1024 + 7])  # 일부만 보내고 연결 종료
                self.wfile.flush()
                self.connection.close()
            else:
                self.wfile.write(PAYLOAD)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/detect.tflite", state
    server.shutdown()


@pytest.fixture
def downloader(tmp_path):
    """download()는 모듈 파일 옆에 저장하므로 임시 폴더에 복사본을 만들어 불러온다."""
    shutil.copy(ROOT / "download_assets.py", tmp_path / "download_assets.py")
    spec = importlib.util.spec_from_file_location("download_assets_copy", tmp_path / "download_assets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, tmp_path


def test_complete_download(asset_server, downloader):
    url, _ = asset_server
    module, folder = downloader
    module.download("detect.tflite", url)
    assert (folder / "detect.tflite").read_bytes() == PAYLOAD
    assert not (folder / "detect.tflite.part").exists()


def test_interrupted_download_leaves_no_file_and_retries(asset_server, downloader):
    url, state = asset_server
    module, folder = downloader
    state["broken"] = True
    with pytest.raises(OSError):
        module.download("detect.tflite", url)
    assert not (folder / "detect.tflite").exists()
    assert not (folder / "detect.tflite.part").exists()

    state["broken"] = False
    module.download("detect.tflite", url)  # 손상 파일이 남지 않았으므로 SKIP하지 않고 다시 받는다
    assert (folder / "detect.tflite").read_bytes() == PAYLOAD


def test_existing_file_is_skipped(asset_server, downloader, capsys):
    url, _ = asset_server
    module, folder = downloader
    (folder / "detect.tflite").write_bytes(b"existing")
    module.download("detect.tflite", url)
    assert (folder / "detect.tflite").read_bytes() == b"existing"
    assert "[SKIP]" in capsys.readouterr().out
