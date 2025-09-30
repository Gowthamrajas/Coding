"""High level utilities for sanitizing, encoding and decoding prompts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .cipher import PromptCipher
from .detector import SensitiveInfoDetector, SensitiveMatch


@dataclass
class EncodedPrompt:
    """Container returned by :class:`PromptGuard` after encoding a prompt."""

    encoded_payload: str
    matches: List[SensitiveMatch]


class PromptGuard:
    """Coordinate detection, masking and encoding of prompts."""

    def __init__(
        self,
        *,
        secret: str,
        detector: Optional[SensitiveInfoDetector] = None,
    ) -> None:
        self.cipher = PromptCipher(secret)
        self.detector = detector or SensitiveInfoDetector(SensitiveInfoDetector.default_patterns())

    def prepare_prompt(self, prompt: str) -> EncodedPrompt:
        """Detect sensitive data, mask it and return the encoded payload."""

        sanitized, matches = self.detector.mask(prompt)
        encoded = self.cipher.encrypt(sanitized)
        return EncodedPrompt(encoded_payload=encoded, matches=list(matches))

    def recover_response(self, encoded_response: str, matches: Iterable[SensitiveMatch]) -> str:
        """Decode a response and restore previously masked values."""

        decoded = self.cipher.decrypt(encoded_response)
        restored = self.detector.restore(decoded, list(matches))
        return restored
