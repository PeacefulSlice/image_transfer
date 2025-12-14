from __future__ import annotations
import json
import socket
from typing import Dict, Tuple

from .config import DELIMITER, HEADER_MAX_BYTES, CHUNK_SIZE
from .exceptions import ProtocolError

def encode_header(header: Dict) -> bytes:
    data = json.dumps(header, ensure_ascii=False).encode("utf-8")
    if len(data) > HEADER_MAX_BYTES:
        raise ProtocolError("Header too large")
    return data + DELIMITER

def recv_until_delimiter(sock: socket.socket) -> Tuple[bytes, bytes]:
    """
    Returns (header_bytes_without_delim, remainder_bytes_after_delim)
    """
    buffer = bytearray()
    while True:
        chunk = sock.recv(CHUNK_SIZE)
        if not chunk:
            raise ProtocolError("Connection closed before header delimiter")
        buffer.extend(chunk)
        if DELIMITER in buffer:
            idx = buffer.index(DELIMITER)
            header = bytes(buffer[:idx])
            rest = bytes(buffer[idx + len(DELIMITER):])
            return header, rest
        if len(buffer) > HEADER_MAX_BYTES:
            raise ProtocolError("Header exceeds max size")

def decode_header(header_bytes: bytes) -> Dict:
    try:
        return json.loads(header_bytes.decode("utf-8"))
    except Exception as e:
        raise ProtocolError(f"Invalid header JSON: {e}") from e

def send_file(sock: socket.socket, file_path: str, chunk_size: int = CHUNK_SIZE) -> None:
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sock.sendall(chunk)

def recv_exact_to_file(sock: socket.socket, total_bytes: int, out_path: str, initial: bytes = b"") -> int:
    """
    Receives exactly total_bytes and writes to out_path.
    Returns number of bytes written.
    """
    written = 0
    with open(out_path, "wb") as f:
        if initial:
            take = initial[:total_bytes]
            f.write(take)
            written += len(take)

        while written < total_bytes:
            to_read = min(CHUNK_SIZE, total_bytes - written)
            chunk = sock.recv(to_read)
            if not chunk:
                break
            f.write(chunk)
            written += len(chunk)
    return written
