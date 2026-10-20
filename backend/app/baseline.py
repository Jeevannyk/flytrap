"""Stand-in for a conventional text filter: flags text containing known injection phrases.

This is a simple keyword filter, NOT an LLM judge. Real LLM judges are stronger, so
treat comparisons against this as a lower bound on what a conventional filter can do.
"""
import re

PATTERNS = [
    r"ignore (all |your |any )?(previous |prior |above )?(instructions|user)",
    r"disregard",
    r"system prompt",
    r"you are now",
]
_RE = re.compile("|".join(PATTERNS), re.I)


def flags(text):
    return bool(_RE.search(text))
