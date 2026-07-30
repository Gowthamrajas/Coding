"""Basic tests for Prompt Guard."""
from __future__ import annotations

from prompt_guard import PromptGuard, check_prompt
from prompt_guard.detector import SensitiveInfoDetector
from prompt_guard.hook import hook_response
from prompt_guard.patterns import resolve_patterns


def test_detects_email_and_client_name() -> None:
    result = check_prompt("Email finance@acme.com about Acme Corp revenue $5M")
    labels = {match["label"] for match in result["matches"]}
    assert "email" in labels
    assert "client_name" in labels
    assert result["safe"] is False


def test_mask_and_restore_round_trip() -> None:
    detector = SensitiveInfoDetector(resolve_patterns())
    original = "Contact john.doe@acme.com for Acme Corp"
    sanitized, matches = detector.mask(original)
    assert "{{SENSITIVE_" in sanitized
    restored = detector.restore(sanitized, matches)
    assert restored == original


def test_hook_blocks_sensitive_prompt() -> None:
    response = hook_response("My OpenAI key is sk-abcdefghijklmnopqrstuvwxyz1234567890abcd")
    assert response["continue"] is False
    assert "user_message" in response


def test_hook_allows_clean_prompt() -> None:
    response = hook_response("Explain binary search in Python")
    assert response["continue"] is True


def test_encode_and_recover() -> None:
    guard = PromptGuard(secret="test-secret")
    encoded = guard.prepare_prompt("Acme Corp revenue $5M")
    fake_response = guard.cipher.encrypt("Report for {{SENSITIVE_1}} approved.")
    restored = guard.recover_response(fake_response, encoded.matches)
    assert "Acme Corp" in restored
