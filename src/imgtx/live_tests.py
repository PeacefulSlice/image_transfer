# src/imgtx/live_tests.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import hashlib

@dataclass
class TestResult:
    name: str
    ok: bool
    details: str = ""
    data: Optional[dict[str, Any]] = None

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sender_preflight(image_path: str) -> tuple[list[TestResult], dict[str, Any]]:
    """Повертає (результати тестів, метадані для передачі/порівняння)."""
    p = Path(image_path)
    results: list[TestResult] = []
    meta: dict[str, Any] = {"path": str(p)}

    results.append(TestResult("File exists", p.exists(), str(p)))
    if not p.exists():
        return results, meta

    try:
        size = p.stat().st_size
        results.append(TestResult("Readable + size", True, f"{size} bytes"))
        meta["size_bytes"] = size
    except Exception as e:
        results.append(TestResult("Readable + size", False, str(e)))
        return results, meta

    try:
        digest = sha256_file(p)
        results.append(TestResult("SHA-256 computed", True, digest))
        meta["sha256"] = digest
    except Exception as e:
        results.append(TestResult("SHA-256 computed", False, str(e)))

    # Pillow validate
    try:
        from PIL import Image
        with Image.open(p) as img:
            img.verify()
        with Image.open(p) as img:
            fmt = img.format
            w, h = img.size
            mode = img.mode
        results.append(TestResult("PIL open/verify", True, f"{fmt} {w}x{h} mode={mode}",
                                  data={"format": fmt, "w": w, "h": h, "mode": mode}))
        meta.update({"format": fmt, "w": w, "h": h, "mode": mode})
    except Exception as e:
        results.append(TestResult("PIL open/verify", False, str(e)))

    return results, meta

def receiver_postflight(saved_path: str, expected: dict[str, Any] | None = None) -> list[TestResult]:
    p = Path(saved_path)
    results: list[TestResult] = []
    expected = expected or {}

    results.append(TestResult("File saved", p.exists(), str(p)))
    if not p.exists():
        return results

    try:
        got_size = p.stat().st_size
        results.append(TestResult("Size computed", True, f"{got_size} bytes"))
        if "size_bytes" in expected:
            exp = int(expected["size_bytes"])
            results.append(TestResult("Size match", got_size == exp,
                                      "match" if got_size == exp else f"expected={exp}, got={got_size}"))
    except Exception as e:
        results.append(TestResult("Size computed", False, str(e)))

    try:
        got_sha = sha256_file(p)
        results.append(TestResult("SHA-256 computed", True, got_sha))
        if "sha256" in expected:
            exp = str(expected["sha256"])
            results.append(TestResult("SHA-256 match", got_sha == exp,
                                      "match" if got_sha == exp else f"expected={exp}, got={got_sha}"))
    except Exception as e:
        results.append(TestResult("SHA-256 computed", False, str(e)))

    try:
        from PIL import Image
        with Image.open(p) as img:
            img.verify()
        with Image.open(p) as img:
            fmt = img.format
            w, h = img.size
            mode = img.mode
        results.append(TestResult("PIL open/verify", True, f"{fmt} {w}x{h} mode={mode}"))
        # якщо sender передавав метадані — порівняємо
        if "format" in expected:
            results.append(TestResult("Format match", fmt == expected["format"], f"expected={expected['format']}, got={fmt}"))
        if "w" in expected and "h" in expected:
            results.append(TestResult("Resolution match", (w == expected["w"] and h == expected["h"]),
                                      f"expected={expected['w']}x{expected['h']}, got={w}x{h}"))
    except Exception as e:
        results.append(TestResult("PIL open/verify", False, str(e)))

    return results
