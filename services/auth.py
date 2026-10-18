"""Contraseñas: se guarda un hash con salt, nunca la contraseña."""

from __future__ import annotations

import hashlib
import hmac
import os

ITERACIONES = 200_000


def crear_hash(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), ITERACIONES
    )
    return h.hex(), salt


def verificar(password: str, password_hash: str, salt: str) -> bool:
    h, _ = crear_hash(password, salt)
    return hmac.compare_digest(h, password_hash)
