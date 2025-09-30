# Prompt Guard

A lightweight Python toolkit that screens prompts for sensitive information,
replaces those segments with deterministic placeholders, and encrypts the
sanitized payload before it is sent to a prompt engine.  Responses can be
decrypted and restored to their original form once the model reply is received.

## Features

- Configurable regular-expression based detector for client names, KPI metrics,
  account numbers, and emails.
- Deterministic placeholder mapping that keeps track of sensitive values.
- Simple symmetric cipher (XOR with SHA-256 derived keystream) to obfuscate
  sanitized payloads without third-party dependencies.
- High-level pipeline class that coordinates detection, masking, encryption, and
  response restoration.

## Quick start

```bash
python -m prompt_guard.example
```

The example script prints the encoded payload, the detected matches, and the
decoded response, illustrating how the placeholders are restored.

## Usage

```python
from prompt_guard import PromptGuard

guard = PromptGuard(secret="your-shared-secret")
user_prompt = "Share ARR forecast for Acme Corp and email finance@acme.com"

encoded_prompt = guard.prepare_prompt(user_prompt)
# -> encoded_prompt.encoded_payload contains the encrypted text ready for the model
# -> encoded_prompt.matches keeps the placeholder metadata

# Send encoded_prompt.encoded_payload to your prompt engine...

# Once the model replies, decrypt and restore:
model_response = guard.recover_response(encoded_payload_from_model, encoded_prompt.matches)
```

> **Security note:** the bundled cipher is intended as a transport obfuscation
> layer to keep the example self-contained.  Replace it with a production-grade
> encryption mechanism and managed key infrastructure when handling real-world
> confidential information.
