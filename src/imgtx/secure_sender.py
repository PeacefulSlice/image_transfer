from __future__ import annotations
import socket, time, secrets
from pathlib import Path
from typing import Dict, Any

from .secure_crypto import encrypt
from .secure_protocol import pack_header

class SecureSender:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    def send_image(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        data = p.read_bytes()

        session_id = secrets.token_hex(16)
        ts = int(time.time())

        # AAD: те, що буде автентифіковано (захист від підміни заголовка)
        aad_dict = {"session_id": session_id, "ts": ts, "filename": p.name}
        aad = str(aad_dict).encode("utf-8")

        salt, nonce, ct = encrypt(self.password, data, aad)

        header = {
            "mode": "aesgcm+scrypt",
            "session_id": session_id,
            "ts": ts,
            "filename": p.name,
            "salt": salt.hex(),
            "nonce": nonce.hex(),
            "aad": aad_dict,           # receiver відтворить AAD
            "cipher_len": len(ct),
        }

        payload = pack_header(header) + ct

        with socket.create_connection((self.host, self.port), timeout=5) as s:
            s.sendall(payload)

        return header
