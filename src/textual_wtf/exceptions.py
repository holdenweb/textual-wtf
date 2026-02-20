"""Exceptions for textual-wtf."""
from __future__ import annotations


class ValidationError(Exception):
    """Raised when a validator or Field.clean() rejects a value."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FieldError(Exception):
    """Raised when field configuration is invalid."""


class FormError(Exception):
    """Raised on form definition or rendering errors."""


class AmbiguousFieldError(Exception):
    """Raised when an unqualified name matches more than one field."""

    def __init__(self, name: str, candidates: list[str]) -> None:
        self.name = name
        self.candidates = candidates
        super().__init__(
            f"'{name}' is ambiguous; matches: {', '.join(candidates)}"
        )
