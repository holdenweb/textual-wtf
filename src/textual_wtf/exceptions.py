"""Exception classes for textual-wtf."""

from __future__ import annotations


class ValidationError(Exception):
    """Raised when a validator or clean() rejects a value."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FieldError(Exception):
    """Raised when field configuration is invalid."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FormError(Exception):
    """Raised for form definition or rendering errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AmbiguousFieldError(Exception):
    """Raised when unqualified attribute access matches multiple fields."""

    def __init__(self, name: str, candidates: list[str]) -> None:
        self.name = name
        self.candidates = candidates
        self.message = f"Ambiguous field name {name!r}: matches {candidates}"
        super().__init__(self.message)
