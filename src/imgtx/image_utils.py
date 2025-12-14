from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import hashlib

from .exceptions import InvalidImageError

@dataclass(frozen=True)
class ImageInfo:
    format: str
    width: int
    height: int
    mode: str

def validate_image(path: str | Path) -> ImageInfo:
    p = Path(path)
    try:
        # verify() перевіряє структуру, але після нього треба відкривати повторно
        with Image.open(p) as img:
            img.verify()

        with Image.open(p) as img2:
            fmt = (img2.format or "").upper()
            w, h = img2.size
            mode = img2.mode
    except (UnidentifiedImageError, OSError) as e:
        raise InvalidImageError(f"File is not a valid image: {p.name}. Reason: {e}") from e

    if not fmt:
        raise InvalidImageError(f"Cannot determine image format for: {p.name}")

    return ImageInfo(format=fmt, width=w, height=h, mode=mode)

def pixel_fingerprint(path: str | Path) -> str:
    """
    'Перевірка відображення' на практиці: декодуємо в пікселі і рахуємо sha256 від RGB байтів.
    Якщо файл декодується і піксельні дані ті самі — fingerprint збігається.
    """
    p = Path(path)
    try:
        with Image.open(p) as img:
            rgb = img.convert("RGB")
            raw = rgb.tobytes()
    except (UnidentifiedImageError, OSError) as e:
        raise InvalidImageError(f"Cannot decode image pixels: {p.name}. Reason: {e}") from e

    return hashlib.sha256(raw).hexdigest()
