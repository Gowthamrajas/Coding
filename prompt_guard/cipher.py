"""Lightweight symmetric cipher for prompt payloads.

The implementation is intentionally simple and avoids external dependencies so
that it can run in restricted environments.  It should be viewed as a transport
obfuscation layer rather than a drop-in replacement for production grade
cryptography.  For sensitive deployments consider using a well vetted library
such as ``cryptography`` and managed keys.
"""
from __future__ import annotations

import base64
import hashlib
from itertools import cycle
from typing import Final


class PromptCipher:
    """Symmetric cipher that performs XOR with a SHA-256 derived key."""

    _BLOCK_SIZE: Final[int] = 32

    def __init__(self, secret: str):
        if not secret:
            raise ValueError("Secret must not be empty")
        self._key = hashlib.sha256(secret.encode("utf-8")).digest()

    def _expand_key(self, length: int) -> bytes:
        return bytes(k for k, _ in zip(cycle(self._key), range(length)))

    def encrypt(self, message: str) -> str:
        data = message.encode("utf-8")
        keystream = self._expand_key(len(data))
        cipher_bytes = bytes(b ^ k for b, k in zip(data, keystream))
        return base64.urlsafe_b64encode(cipher_bytes).decode("ascii")

    def decrypt(self, token: str) -> str:
        data = base64.urlsafe_b64decode(token.encode("ascii"))
        keystream = self._expand_key(len(data))
        plain_bytes = bytes(b ^ k for b, k in zip(data, keystream))
        return plain_bytes.decode("utf-8")
