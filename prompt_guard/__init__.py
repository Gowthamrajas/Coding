"""Prompt Guard package."""

from .detector import SensitiveInfoDetector, SensitiveMatch, SensitivePattern
from .cipher import PromptCipher
from .hook import check_prompt, hook_response
from .patterns import builtin_patterns, resolve_patterns
from .pipeline import PromptGuard, EncodedPrompt

__all__ = [
    "SensitiveInfoDetector",
    "SensitiveMatch",
    "SensitivePattern",
    "PromptCipher",
    "PromptGuard",
    "EncodedPrompt",
    "check_prompt",
    "hook_response",
    "builtin_patterns",
    "resolve_patterns",
]

__version__ = "0.2.0"
