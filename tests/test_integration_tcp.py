import threading
import time
from pathlib import Path

import pytest

from imgtx.receiver import ReceiverServer
from imgtx.sender import Sender
from imgtx.crypto import sha256_file
from imgtx.image_utils import validate_image, pixel_fingerprint

TEST_HOST = "127.0.0.1"
TEST_PORT = 5055

def run_receiver(result_box, out_dir):
    srv = ReceiverServer(host=TEST_HOST, port=TEST_PORT, output_dir=out_dir)
    result_box["res"] = srv.serve_once()

@pytest.mark.timeout(10)
def test_tcp_transfer_ok(tmp_path: Path):
    # Підготуй свій тестовий jpg у tests/assets/sample_ok.jpg
    sample = Path("tests/assets/sample_ok.jpg")
    assert sample.exists(), "Put a JPG here: tests/assets/sample_ok.jpg"

    out_dir = tmp_path / "received"
    out_dir.mkdir(parents=True, exist_ok=True)

    box = {}
    t = threading.Thread(target=run_receiver, args=(box, str(out_dir)), daemon=True)
    t.start()
    time.sleep(0.2)  # дай серверу піднятись

    sender = Sender(host=TEST_HOST, port=TEST_PORT)
    header = sender.send_image(str(sample))

    t.join(timeout=8)
    assert "res" in box, "Receiver did not return result"

    res = box["res"]
    saved = Path(res.saved_path)
    assert saved.exists()

    # 1) Байтовий SHA співпадає
    assert sha256_file(sample) == sha256_file(saved)

    # 2) Валідація як зображення
    a = validate_image(sample)
    b = validate_image(saved)
    assert (a.format, a.width, a.height) == (b.format, b.width, b.height)

    # 3) Перевірка "відображення" — піксельний fingerprint
    assert pixel_fingerprint(sample) == pixel_fingerprint(saved)

    # (додатково) метадані з хедера
    assert header["width"] == b.width
    assert header["height"] == b.height
