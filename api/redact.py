"""Credential scrubbing.

Anything that leaves the server — logs, error messages, tracebacks — passes
through here first. Two layers:

1. Exact replacement of every configured secret value (API keys, tokens, project
   ids, model ids) with `[REDACTED]`.
2. Pattern-based scrubbing for key-shaped strings that were never in our
   environment, so a failure from a third-party library cannot leak one.

The scrubber never logs or returns the values it is protecting.
"""

from __future__ import annotations

import re

REDACTED = "[REDACTED]"

# Conservative, high-signal patterns. Deliberately narrow so ordinary prose and
# tracebacks are not mangled.
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Bearer / authorization headers
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]{12,}"), r"\1 " + REDACTED),
    # OpenAI/Nebius-style prefixed keys
    (re.compile(r"\b(sk|pk|api|key)[-_][A-Za-z0-9]{16,}"), REDACTED),
    # JWTs
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{6,}"), REDACTED),
    # Long opaque hex/base64 blobs that look like credentials
    (re.compile(r"\b[A-Fa-f0-9]{40,}\b"), REDACTED),
    # Explicit key=value forms in logs
    (
        re.compile(
            r"(?i)\b(api[_-]?key|token|secret|password|authorization)"
            r"\s*[=:]\s*[\"']?([^\s\"',;]{8,})"
        ),
        r"\1=" + REDACTED,
    ),
)


class SecretScrubber:
    """Replaces known secret values and key-shaped strings."""

    def __init__(self, secrets: list[str] | None = None) -> None:
        # Longest first so a secret containing another is replaced whole.
        self._secrets = sorted({s for s in (secrets or []) if len(s) >= 8}, key=len, reverse=True)

    def scrub(self, text: str | None) -> str:
        if not text:
            return ""
        out = str(text)
        for secret in self._secrets:
            out = out.replace(secret, REDACTED)
        for pattern, replacement in _PATTERNS:
            out = pattern.sub(replacement, out)
        return out

    def scrub_lines(self, lines: list[str]) -> list[str]:
        return [self.scrub(line) for line in lines]

    def contains_secret(self, text: str | None) -> bool:
        """Used by tests to assert nothing leaked."""
        if not text:
            return False
        payload = str(text)
        return any(secret in payload for secret in self._secrets)

    def __repr__(self) -> str:  # never expose the values
        return f"SecretScrubber({len(self._secrets)} secret(s))"
