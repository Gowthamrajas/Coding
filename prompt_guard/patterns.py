"""Shared sensitive-data pattern definitions."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Pattern, Sequence, Tuple

from .detector import SensitivePattern


def builtin_patterns() -> Tuple[SensitivePattern, ...]:
    """Return the full built-in pattern set for business and credential data."""

    client_names = (
        r"\b(?:Acme Corp|Globex|Initech|Umbrella|Hooli|Vehement Capital Partners)\b"
    )
    kpi_values = (
        r"\b(?:revenue|ebitda|profit|conversion rate|churn rate|"
        r"net promoter score|ARR|customer acquisition cost)\b[^\n]*?\d[\w$%,.-]*"
    )
    card_like = r"\b(?:\d[ -]?){13,16}\b"
    email_like = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    private_key = r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"
    cursor_api_key = r"(?:^|[^A-Za-z0-9_-])crsr_[A-Za-z0-9_-]{20,}(?:[^A-Za-z0-9_-]|$)"
    github_token = (
        r"(?:^|[^A-Za-z0-9_])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}(?:[^A-Za-z0-9_]|$)"
    )
    slack_token = r"(?:^|[^A-Za-z0-9_-])xox[baprs]-[A-Za-z0-9-]{20,}(?:[^A-Za-z0-9_-]|$)"
    openai_key = r"(?:^|[^A-Za-z0-9_-])sk-[A-Za-z0-9_-]{32,}(?:[^A-Za-z0-9_-]|$)"
    aws_key = r"(?:^|[^A-Za-z0-9_])(?:AKIA|ASIA)[A-Z0-9]{16}(?:[^A-Za-z0-9_]|$)"
    jwt_like = (
        r"(?:^|[^A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{10,}\."
        r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?:[^A-Za-z0-9_-]|$)"
    )
    ssn_like = r"\b\d{3}-\d{2}-\d{4}\b"
    phone_like = r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"

    return (
        SensitivePattern("client_name", re.compile(client_names, re.IGNORECASE)),
        SensitivePattern("kpi", re.compile(kpi_values, re.IGNORECASE)),
        SensitivePattern("possible_account_number", re.compile(card_like)),
        SensitivePattern("email", re.compile(email_like)),
        SensitivePattern("private_key", re.compile(private_key)),
        SensitivePattern("cursor_api_key", re.compile(cursor_api_key)),
        SensitivePattern("github_token", re.compile(github_token)),
        SensitivePattern("slack_token", re.compile(slack_token)),
        SensitivePattern("openai_api_key", re.compile(openai_key)),
        SensitivePattern("aws_access_key", re.compile(aws_key)),
        SensitivePattern("jwt_token", re.compile(jwt_like)),
        SensitivePattern("ssn", re.compile(ssn_like)),
        SensitivePattern("phone_number", re.compile(phone_like)),
    )


def load_custom_patterns(config_path: Path) -> Tuple[SensitivePattern, ...]:
    """Load user-defined regex patterns from a JSON config file."""

    if not config_path.is_file():
        return ()

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    entries = raw.get("patterns", raw if isinstance(raw, list) else [])
    patterns: List[SensitivePattern] = []
    for entry in entries:
        label = entry["label"]
        regex = entry["pattern"]
        flags = 0
        if entry.get("ignore_case", False):
            flags |= re.IGNORECASE
        patterns.append(SensitivePattern(label, re.compile(regex, flags)))
    return tuple(patterns)


def resolve_patterns(
    *,
    config_paths: Iterable[Path] | None = None,
    include_builtin: bool = True,
) -> Tuple[SensitivePattern, ...]:
    """Merge built-in and project/user custom patterns."""

    patterns: List[SensitivePattern] = []
    if include_builtin:
        patterns.extend(builtin_patterns())

    search_paths = list(config_paths or default_config_paths())
    seen_labels = {pattern.label for pattern in patterns}
    for path in search_paths:
        for custom in load_custom_patterns(path):
            if custom.label in seen_labels:
                continue
            patterns.append(custom)
            seen_labels.add(custom.label)
    return tuple(patterns)


def default_config_paths() -> Sequence[Path]:
    """Return config locations checked in priority order."""

    candidates = [
        Path.cwd() / ".prompt-guard.json",
        Path.home() / ".prompt-guard" / "config.json",
    ]
    return tuple(path for path in candidates if path.is_file())
