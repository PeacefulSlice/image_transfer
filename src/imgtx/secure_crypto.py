from __future__ import annotations
import os, time, json, secrets
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_LEN = 32           # AES-256
SALT_LEN = 16
NONCE_LEN = 12         # recommended for GCM

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_LEN, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))

def encrypt(password: str, plaintext: bytes, aad: bytes) -> Tuple[bytes, bytes, bytes]:
    salt = os.urandom(SALT_LEN)
    key = derive_key(password, salt)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, plaintext, aad)  # ct includes tag
    return salt, nonce, ct

def decrypt(password: str, salt: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    key = derive_key(password, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, aad)  # raises if tag mismatch
