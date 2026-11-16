#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen

ASSETS = {
    "detect.tflite": "https://raw.githubusercontent.com/Qengineering/TensorFlow_Lite_SSD_RPi_64-bits/master/detect.tflite",
    "James.mp4": "https://raw.githubusercontent.com/Qengineering/TensorFlow_Lite_SSD_RPi_64-bits/master/James.mp4",
}

def download(name, url):
    dest = Path(__file__).resolve().parent / name
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[SKIP] {name} already exists ({dest.stat().st_size / 1024 / 1024:.1f} MB)")
        return

    print(f"[GET ] {name}")
    # 임시 파일에 받은 뒤 크기를 확인하고 교체한다. 중간에 끊긴 파일이 완성본처럼 남아 다음 실행에서 SKIP되는 것을 막는다.
    part = dest.with_name(dest.name + ".part")
    req = Request(url, headers={"User-Agent": "object-tracking-pc"})
    try:
        with urlopen(req) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r      {done * 100 / total:5.1f}%  {done / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB", end="")
            if total:
                print()
        if done == 0 or (total and done != total):
            raise IOError(f"{name} 다운로드가 완료되지 않았습니다 ({done}/{total or '?'} bytes)")
        part.replace(dest)
    finally:
        if part.exists():
            part.unlink()

    print(f"[DONE] {dest.name} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")

def main():
    for name, url in ASSETS.items():
        download(name, url)
    print("Assets ready.")

if __name__ == "__main__":
    main()
