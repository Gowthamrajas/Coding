"""Example usage of the prompt guard pipeline."""
from __future__ import annotations

from .pipeline import PromptGuard


def run_example() -> None:
    guard = PromptGuard(secret="demo-secret")
    prompt = (
        "Draft a client update for Acme Corp. Include revenue: $5.2M, "
        "net promoter score 62%, and email john.doe@acme.com for approval."
    )

    encoded = guard.prepare_prompt(prompt)
    print("Encoded payload:", encoded.encoded_payload)
    print("Detected matches:")
    for match in encoded.matches:
        print(f" - {match.label}: {match.value} -> {match.placeholder}")

    # Simulate model response by echoing the sanitized prompt.
    fake_model_response = guard.cipher.encrypt(
        "The update for {{SENSITIVE_1}} with {{SENSITIVE_2}} was approved by {{SENSITIVE_4}}."
    )

    decoded = guard.recover_response(fake_model_response, encoded.matches)
    print("Decoded response:", decoded)


if __name__ == "__main__":
    run_example()
