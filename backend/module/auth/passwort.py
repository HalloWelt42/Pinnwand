"""Passwort-Hashing mit der Standardbibliothek (kein externes Paket).

Format: ``pbkdf2_sha256$<iterationen>$<salt_hex>$<hash_hex>``. Pro Passwort ein
eigener Zufalls-Salt; Vergleich konstantzeitig. Bewusst schlicht und lokal -
ausreichend fuer eine lokale Mehrbenutzer-Pinnwand, ohne Fremdabhaengigkeit.
"""
from __future__ import annotations

import hashlib
import hmac
import os

_ALGO = "pbkdf2_sha256"
_ITERATIONEN = 210_000


def hash_passwort(klartext: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", klartext.encode("utf-8"), salt, _ITERATIONEN)
    return f"{_ALGO}${_ITERATIONEN}${salt.hex()}${dk.hex()}"


def pruefe(klartext: str, gespeichert: str | None) -> bool:
    """True, wenn das Klartext-Passwort zum gespeicherten Hash passt."""
    if not gespeichert:
        return False
    try:
        algo, iter_s, salt_hex, hash_hex = gespeichert.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac("sha256", klartext.encode("utf-8"), bytes.fromhex(salt_hex), int(iter_s))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False
