from __future__ import annotations
import json, struct, time, secrets
from dataclasses import dataclass
from typing import Dict, Any

def pack_header(h: Dict[str, Any]) -> bytes:
    raw = json.dumps(h, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return struct.pack(">I", len(raw)) + raw

def recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed")
        buf += chunk
    return buf

def recv_header(sock) -> Dict[str, Any]:
    ln = struct.unpack(">I", recv_exact(sock, 4))[0]
    raw = recv_exact(sock, ln)
    return json.loads(raw.decode("utf-8"))
