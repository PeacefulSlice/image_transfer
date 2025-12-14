from __future__ import annotations
import os
import socket
from pathlib import Path
from dataclasses import dataclass

from .config import DEFAULT_HOST, DEFAULT_PORT, VERSION
from .protocol import recv_until_delimiter, decode_header, recv_exact_to_file
from .crypto import sha256_file
from .image_utils import validate_image, pixel_fingerprint
from .exceptions import ProtocolError, IntegrityError, InvalidImageError

@dataclass(frozen=True)
class ReceiveResult:
    saved_path: str
    sha256: str
    pixel_fp: str
    width: int
    height: int
    format: str

class ReceiverServer:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, output_dir: str = "outputs/received"):
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def serve_once(self) -> ReceiveResult:
        """
        Прийняти ОДНЕ зображення і завершитися (ідеально для інтеграційних тестів).
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(1)
            conn, _addr = s.accept()
            with conn:
                return self._handle_client(conn)

    def _handle_client(self, conn: socket.socket) -> ReceiveResult:
        header_bytes, rest = recv_until_delimiter(conn)
        header = decode_header(header_bytes)

        if int(header.get("version", -1)) != VERSION:
            raise ProtocolError("Unsupported protocol version")

        filename = str(header.get("filename", "image"))
        size_bytes = int(header["size_bytes"])
        expected_sha = str(header["sha256"]).lower()

        tmp_path = self.output_dir / (".tmp_" + filename)
        written = recv_exact_to_file(conn, size_bytes, str(tmp_path), initial=rest)

        if written != size_bytes:
            # неповна передача
            raise IntegrityError(f"Incomplete transfer: expected {size_bytes}, got {written}")

        actual_sha = sha256_file(tmp_path)
        if actual_sha.lower() != expected_sha:
            raise IntegrityError("SHA256 mismatch (data corrupted)")

        # валідність зображення + метадані
        info = validate_image(tmp_path)

        hdr_w = int(header.get("width", info.width))
        hdr_h = int(header.get("height", info.height))
        if (info.width, info.height) != (hdr_w, hdr_h):
            raise InvalidImageError("Image dimensions mismatch")

        # fingerprint "відображення"
        px = pixel_fingerprint(tmp_path)

        safe_name = f"{actual_sha[:12]}__{os.path.basename(filename)}"
        final_path = self.output_dir / safe_name
        tmp_path.replace(final_path)

        return ReceiveResult(
            saved_path=str(final_path),
            sha256=actual_sha,
            pixel_fp=px,
            width=info.width,
            height=info.height,
            format=info.format,
        )
