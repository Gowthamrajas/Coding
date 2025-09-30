"""Utilities for identifying and masking sensitive information in prompts."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Pattern, Sequence, Tuple


@dataclass(frozen=True)
class SensitivePattern:
    """Configuration for a sensitive information pattern."""

    label: str
    pattern: Pattern[str]


@dataclass(frozen=True)
class SensitiveMatch:
    """Represents a single sensitive segment detected in a prompt."""

    label: str
    value: str
    placeholder: str
    start: int
    end: int


class SensitiveInfoDetector:
    """Detects and masks sensitive entities inside prompts."""

    def __init__(self, patterns: Iterable[SensitivePattern]):
        patterns = tuple(patterns)
        if not patterns:
            raise ValueError("At least one SensitivePattern is required")
        self._patterns: Tuple[SensitivePattern, ...] = patterns

    @staticmethod
    def default_patterns() -> Tuple[SensitivePattern, ...]:
        """Return a curated set of default detection rules."""

        client_names = r"\b(?:Acme Corp|Globex|Initech|Umbrella|Hooli|Vehement Capital Partners)\b"
        kpi_values = (
            r"\b(?:revenue|ebitda|profit|conversion rate|churn rate|"
            r"net promoter score|ARR|customer acquisition cost)\b[^\n]*?\d[\w$%,.-]*"
        )
        card_like = r"\b(?:\d[ -]?){13,16}\b"
        email_like = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        return (
            SensitivePattern("client_name", re.compile(client_names, re.IGNORECASE)),
            SensitivePattern("kpi", re.compile(kpi_values, re.IGNORECASE)),
            SensitivePattern("possible_account_number", re.compile(card_like)),
            SensitivePattern("email", re.compile(email_like)),
        )

    def scan(self, text: str) -> List[SensitiveMatch]:
        """Scan ``text`` for sensitive information and return the matches."""

        spans: List[Tuple[int, int, SensitivePattern, str]] = []
        for pattern in self._patterns:
            for match in pattern.pattern.finditer(text):
                spans.append((match.start(), match.end(), pattern, match.group(0)))

        spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))

        matches: List[SensitiveMatch] = []
        last_end = -1
        counter = 1
        for start, end, pattern, value in spans:
            if start < last_end:
                # Skip overlapping matches, keep the earliest occurrence.
                continue
            placeholder = f"{{{{SENSITIVE_{counter}}}}}"
            matches.append(
                SensitiveMatch(
                    label=pattern.label,
                    value=value,
                    placeholder=placeholder,
                    start=start,
                    end=end,
                )
            )
            counter += 1
            last_end = end
        return matches

    def mask(self, text: str) -> Tuple[str, List[SensitiveMatch]]:
        """Mask sensitive segments in ``text`` and return the sanitized prompt."""

        matches = self.scan(text)
        if not matches:
            return text, []

        result_parts = []
        last_idx = 0
        for match in matches:
            result_parts.append(text[last_idx:match.start])
            result_parts.append(match.placeholder)
            last_idx = match.end
        result_parts.append(text[last_idx:])

        sanitized = "".join(result_parts)
        return sanitized, matches

    def restore(self, text: str, matches: Sequence[SensitiveMatch]) -> str:
        """Restore previously masked placeholders with their original values."""

        restored = text
        for match in matches:
            restored = restored.replace(match.placeholder, match.value)
        return restored
