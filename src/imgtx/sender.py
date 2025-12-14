from __future__ import annotations
import socket
from pathlib import Path

from .config import DEFAULT_HOST, DEFAULT_PORT, VERSION
from .crypto import sha256_file
from .image_utils import validate_image, pixel_fingerprint
from .protocol import encode_header, send_file

class Sender:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port

    def send_image(self, path: str) -> dict:
        p = Path(path)
        info = validate_image(p)
        digest = sha256_file(p)
        px = pixel_fingerprint(p)

        header = {
            "version": VERSION,
            "filename": p.name,
            "content_type": self._content_type_from_format(info.format),
            "size_bytes": p.stat().st_size,
            "sha256": digest,
            "width": info.width,
            "height": info.height,
            "pixel_fp": px,  # корисно для тестів/логів (можна не використовувати на приймачі)
        }

        payload = encode_header(header)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(payload)
            send_file(s, str(p))

        return header

    @staticmethod
    def _content_type_from_format(fmt: str) -> str:
        fmt = fmt.upper()
        if fmt == "JPEG":
            return "image/jpeg"
        if fmt == "PNG":
            return "image/png"
        return f"image/{fmt.lower()}"
