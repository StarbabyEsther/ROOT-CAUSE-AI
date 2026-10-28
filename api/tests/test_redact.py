"""Credential scrubbing — nothing sensitive may leave the server."""

from __future__ import annotations

from api.redact import REDACTED, SecretScrubber

SECRET = "nebius-SECRET-key-0123456789abcdef"


def test_known_secret_is_removed():
    scrubber = SecretScrubber([SECRET])
    assert SECRET not in scrubber.scrub(f"token is {SECRET} ok")


def test_short_values_are_not_treated_as_secrets():
    scrubber = SecretScrubber(["abc"])
    assert scrubber.scrub("abc def") == "abc def"


def test_bearer_header_is_scrubbed():
    scrubber = SecretScrubber([])
    assert "abc123" not in scrubber.scrub("Authorization: Bearer abc123def456ghi789")


def test_key_value_forms_are_scrubbed():
    scrubber = SecretScrubber([])
    text = "config api_key=super-secret-value-1 token: another-secret-2"
    scrubbed = scrubber.scrub(text)
    assert "super-secret-value-1" not in scrubbed
    assert "another-secret-2" not in scrubbed


def test_traceback_is_scrubbed_but_readable():
    scrubber = SecretScrubber([SECRET])
    text = f'Traceback (most recent call last):\n  File "x.py", line 1\nRuntimeError: bad key {SECRET}'
    scrubbed = scrubber.scrub(text)
    assert SECRET not in scrubbed
    assert "Traceback" in scrubbed
    assert REDACTED in scrubbed


def test_contains_secret_helper():
    scrubber = SecretScrubber([SECRET])
    assert scrubber.contains_secret(f"leak {SECRET}")
    assert not scrubber.contains_secret("clean text")


def test_repr_never_exposes_values():
    scrubber = SecretScrubber([SECRET])
    assert SECRET not in repr(scrubber)
