"""Subject-specific prompts with embedded rules."""

from .ukrainian_rules import UKRAINIAN_RULES, get_ukrainian_mega_prompt
from .algebra_rules import ALGEBRA_RULES, get_algebra_mega_prompt
from .history_rules import HISTORY_RULES, get_history_mega_prompt

__all__ = [
    "UKRAINIAN_RULES",
    "get_ukrainian_mega_prompt",
    "ALGEBRA_RULES",
    "get_algebra_mega_prompt",
    "HISTORY_RULES",
    "get_history_mega_prompt",
]
