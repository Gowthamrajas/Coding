"""Cursor/IDE hook entrypoint for blocking sensitive prompt submissions."""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from .detector import SensitiveInfoDetector
from .patterns import resolve_patterns


def check_prompt(text: str) -> Dict[str, Any]:
    """Scan text and return a structured result."""

    detector = SensitiveInfoDetector(resolve_patterns())
    matches = detector.scan(text)
    return {
        "safe": not matches,
        "match_count": len(matches),
        "matches": [
            {
                "label": match.label,
                "value": match.value,
                "placeholder": match.placeholder,
            }
            for match in matches
        ],
    }


def hook_response(prompt: str) -> Dict[str, Any]:
    """Build the JSON response expected by Cursor's beforeSubmitPrompt hook."""

    result = check_prompt(prompt)
    if result["safe"]:
        return {"continue": True}

    labels = sorted({match["label"] for match in result["matches"]})
    label_text = ", ".join(labels)
    count = result["match_count"]
    message = (
        f"Prompt Guard blocked this submission: detected {count} sensitive "
        f"segment(s) ({label_text}). Sanitize the prompt first using "
        f"'Prompt Guard: Sanitize Selection' or remove the sensitive values."
    )
    return {"continue": False, "user_message": message}


def main() -> int:
    """Read hook JSON from stdin and write the hook response to stdout."""

    try:
        raw = sys.stdin.read()
        payload: Dict[str, Any] = {}
        if raw.strip():
            payload = json.loads(raw)

        prompt = payload.get("prompt", "")
        response = hook_response(prompt)
        sys.stdout.write(json.dumps(response))
        return 0
    except Exception:
        # Fail open: allow the prompt if the checker itself breaks.
        sys.stdout.write(json.dumps({"continue": True}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
