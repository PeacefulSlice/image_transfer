from __future__ import annotations
import socket, time
from pathlib import Path
from typing import Dict, Any

from .secure_protocol import recv_header, recv_exact
from .secure_crypto import decrypt

class ReplayCache:
    def __init__(self, ttl_sec: int = 300):
        self.ttl = ttl_sec
        self.seen: Dict[str, int] = {}

    def check_and_mark(self, session_id: str, ts: int) -> None:
        now = int(time.time())
        # cleanup
        for k, v in list(self.seen.items()):
            if now - v > self.ttl:
                del self.seen[k]

        if session_id in self.seen:
            raise ValueError("REPLAY_DETECTED")

        # timestamp sanity (±5 min)
        if abs(now - ts) > self.ttl:
            raise ValueError("TIMESTAMP_OUT_OF_WINDOW")

        self.seen[session_id] = now

class SecureReceiverServer:
    def __init__(self, host: str, port: int, output_dir: str, password: str):
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir)
        self.password = password
        self.cache = ReplayCache(ttl_sec=300)

    def serve_once(self) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(1)
            conn, _ = srv.accept()

            with conn:
                header = recv_header(conn)

                session_id = header["session_id"]
                ts = int(header["ts"])
                self.cache.check_and_mark(session_id, ts)

                ct = recv_exact(conn, int(header["cipher_len"]))

                salt = bytes.fromhex(header["salt"])
                nonce = bytes.fromhex(header["nonce"])
                aad_dict = header["aad"]
                aad = str(aad_dict).encode("utf-8")

                # Якщо пароль не той / дані зіпсовані — тут впаде (tag mismatch)
                plaintext = decrypt(self.password, salt, nonce, ct, aad)

                out_name = f"{session_id}__{header['filename']}"
                out_path = self.output_dir / out_name
                out_path.write_bytes(plaintext)

                return str(out_path)
