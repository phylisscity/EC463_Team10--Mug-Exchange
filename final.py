import os, re, time
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

from picamera2 import Picamera2
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ----------------------------- CONFIG ---------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://172.20.10.13:3000/pickup")
OUTDIR      = Path(os.getenv("CAPTURE_DIR", "captures"))
DEBOUNCE_S  = float(os.getenv("DEBOUNCE_S", "0.8"))
CAP_RES     = (1640, 1232)  # use (3280,2464) for max detail (slower)
TESS_CFGS   = [
    "--oem 3 --psm 6 -l eng", 
    "--oem 3 --psm 7 -l eng",  # single text line
]
ROTATIONS   = (0, 270)      
# ----------------------------------------------------------------------

# ---- Robust HTTP session with retries ----
_session = requests.Session()
retry = Retry(
    total=3, backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods={"HEAD", "GET", "OPTIONS", "POST"}
)
_session.mount("http://", HTTPAdapter(max_retries=retry))
_session.mount("https://", HTTPAdapter(max_retries=retry))

# ---------- UID helpers to print Pico-style hex (e.g., "00 D2 87 39") ----------
def int_to_bytes_big(n: int) -> bytes:
    ln = max(4, (n.bit_length() + 7) // 8)
    return n.to_bytes(ln, "big")

def strip_bcc(uid_bytes: bytes) -> bytes:
    if len(uid_bytes) >= 4:
        bcc = 0
        for x in uid_bytes[:-1]:
            bcc ^= x
        if bcc == uid_bytes[-1]:
            return uid_bytes[:-1]
    return uid_bytes

def pi_int_to_pico_hex(pi_val: int) -> str:
    b = int_to_bytes_big(pi_val)   # e.g. D2 87 39 6C
    b = strip_bcc(b)               # -> D2 87 39
    if len(b) == 3:
        b = bytes([0x00, *b])      # -> 00 D2 87 39
    return " ".join(f"{x:02X}" for x in b)
# ----------------------------------------------------------------------

def capture_and_save() -> Path:
    """Capture a JPEG from the Pi camera and save it; return path."""
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTDIR / f"capture_{ts}.jpg"

    cam = Picamera2()
    cam.configure(cam.create_still_configuration(main={"size": CAP_RES, "format": "RGB888"}))
    cam.start()
    time.sleep(1.0)  # let exposure / AWB settle
    arr = cam.capture_array()
    cam.stop()

    Image.fromarray(arr).save(out, "JPEG", quality=92)
    return out

# ---------- OCR helpers ----------
def _preprocess_basic(pil: Image.Image) -> Image.Image:
    """Grayscale → autocontrast → sharpen → upscale → binary (global)."""
    im = pil.convert("L")
    im = ImageOps.autocontrast(im)
    im = im.filter(ImageFilter.SHARPEN)
    im = im.resize((int(im.width * 1.5), int(im.height * 1.5)))
    # global threshold (works well for evenly lit documents)
    thr = 160
    bw = im.point(lambda x: 255 if x > thr else 0, mode="1")
    return bw

def _preprocess_adaptive(pil: Image.Image) -> Image.Image:
    """Alternative path: grayscale → autocontrast → upscale (no hard binarize)."""
    im = pil.convert("L")
    im = ImageOps.autocontrast(im)
    im = im.resize((int(im.width * 1.5), int(im.height * 1.5)))
    return im  # let Tesseract do its own thresholding

def _clean_username(raw: str) -> str:
    """
    Extract a simple 'name' from OCR text.
    - keep letters and spaces
    - take first 1-2 words, capitalized
    """
    # Keep letters/spaces only
    words = re.findall(r"[A-Za-z]+", raw)
    if not words:
        return ""
    if len(words) >= 2:
        cand = f"{words[0]} {words[1]}"
    else:
        cand = words[0]
    return cand.title()

def ocr_username(pil: Image.Image) -> str:
    """Try a couple of rotations & preprocess paths; return best non-empty cleaned name."""
    best = ""
    # Try both rotation angles and both preprocessing paths with a couple tess configs
    for rot in ROTATIONS:
        imr = pil.rotate(rot, expand=True)
        for prep in (_preprocess_basic, _preprocess_adaptive):
            img = prep(imr)
            for cfg in TESS_CFGS:
                text = pytesseract.image_to_string(img, config=cfg)
                name = _clean_username(text)
                if name:
                    return name
    return ""  # if nothing found

def send_scan(mug_id: str, username: str):
    payload = {"mug_id": str(mug_id), "username": username}
    try:
        r = _session.post(BACKEND_URL, json=payload, timeout=5)
        if r.status_code in (200, 201):
            print(f"✅ Sent {payload} | reply:", (r.text or "").strip()[:400])
        else:
            print(f"⚠️ Server returned {r.status_code}: {(r.text or '').strip()[:400]}")
    except requests.RequestException as e:
        print("❌ Network error:", e)

def main():
    print(f"Backend: {BACKEND_URL}")
    print("Ready. Scan a tag… (Ctrl+C to quit)")

    reader = SimpleMFRC522()  # RST default BCM22
    last_uid, last_time = None, 0.0

    try:
        while True:
            uid, _ = reader.read_no_block()
            now = time.time()
            if uid is not None and (uid != last_uid or (now - last_time) > DEBOUNCE_S):
                pico_str = pi_int_to_pico_hex(uid)
                print(f"RFID UID: {uid}  |  Pico-style: {pico_str}")

                print("→ Capturing image…")
                img_path = capture_and_save()
                print(f"Saved: {img_path}")

                # OCR
                pil = Image.open(img_path)
                username = ocr_username(pil)
                if not username:
                    username = "Unknown"
                print(f"OCR username: {username}")

                # Send to backend
                send_scan(str(uid), username)

                last_uid, last_time = uid, now

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting…")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
