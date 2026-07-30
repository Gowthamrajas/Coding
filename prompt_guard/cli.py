"""Command-line interface for Prompt Guard."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable, Sequence

from .detector import SensitiveInfoDetector
from .hook import check_prompt, hook_response
from .patterns import resolve_patterns
from .pipeline import PromptGuard


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-guard",
        description="Detect and mask sensitive data before sending prompts to LLMs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan text for sensitive data")
    scan.add_argument("text", nargs="?", help="Text to scan. Reads stdin when omitted.")
    scan.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    sanitize = subparsers.add_parser("sanitize", help="Mask sensitive segments with placeholders")
    sanitize.add_argument("text", nargs="?", help="Text to sanitize. Reads stdin when omitted.")
    sanitize.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    check = subparsers.add_parser("check", help="Exit 0 when text is safe, 1 when sensitive data is found")
    check.add_argument("text", nargs="?", help="Text to check. Reads stdin when omitted.")
    check.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    hook = subparsers.add_parser(
        "hook",
        help="Cursor beforeSubmitPrompt hook adapter (reads JSON from stdin)",
    )

    encode = subparsers.add_parser("encode", help="Mask and encrypt a prompt payload")
    encode.add_argument("text", nargs="?", help="Prompt text. Reads stdin when omitted.")
    encode.add_argument("--secret", required=True, help="Shared secret for encryption")
    encode.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    return parser


def _read_text(text: str | None) -> str:
    if text is not None:
        return text
    return sys.stdin.read()


def _print_matches_json(result: dict) -> None:
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _cmd_scan(text: str, as_json: bool) -> int:
    result = check_prompt(text)
    if as_json:
        _print_matches_json(result)
        return 0

    if result["safe"]:
        print("No sensitive data detected.")
        return 0

    print(f"Detected {result['match_count']} sensitive segment(s):")
    for match in result["matches"]:
        print(f" - {match['label']}: {match['value']} -> {match['placeholder']}")
    return 0


def _cmd_sanitize(text: str, as_json: bool) -> int:
    detector = SensitiveInfoDetector(resolve_patterns())
    sanitized, matches = detector.mask(text)
    if as_json:
        _print_matches_json(
            {
                "sanitized": sanitized,
                "matches": [
                    {
                        "label": match.label,
                        "value": match.value,
                        "placeholder": match.placeholder,
                    }
                    for match in matches
                ],
            }
        )
        return 0

    print(sanitized)
    if matches:
        print("\n# Replacements", file=sys.stderr)
        for match in matches:
            print(f"# {match.label}: {match.value} -> {match.placeholder}", file=sys.stderr)
    return 0


def _cmd_check(text: str, as_json: bool) -> int:
    result = check_prompt(text)
    if as_json:
        _print_matches_json(result)
    return 0 if result["safe"] else 1


def _cmd_hook() -> int:
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    response = hook_response(payload.get("prompt", ""))
    json.dump(response, sys.stdout)
    return 0


def _cmd_encode(text: str, secret: str, as_json: bool) -> int:
    guard = PromptGuard(secret=secret)
    encoded = guard.prepare_prompt(text)
    if as_json:
        _print_matches_json(
            {
                "encoded_payload": encoded.encoded_payload,
                "matches": [
                    {
                        "label": match.label,
                        "value": match.value,
                        "placeholder": match.placeholder,
                    }
                    for match in encoded.matches
                ],
            }
        )
        return 0

    print(encoded.encoded_payload)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "hook":
        return _cmd_hook()
    if args.command == "encode":
        return _cmd_encode(_read_text(args.text), args.secret, args.json)

    text = _read_text(getattr(args, "text", None))
    if args.command == "scan":
        return _cmd_scan(text, args.json)
    if args.command == "sanitize":
        return _cmd_sanitize(text, args.json)
    if args.command == "check":
        return _cmd_check(text, args.json)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
