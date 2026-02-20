"""Validators for textual-wtf fields."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from .exceptions import ValidationError


class Validator(ABC):
    """Abstract base for class-based validators.

    Alternatively, any callable ``(value: Any) -> None`` that raises
    ``ValidationError`` on failure may be used directly.
    """

    @abstractmethod
    def validate(self, value: Any) -> None:
        """Raise ``ValidationError`` if *value* is invalid."""


class Required(Validator):
    """Value must be non-empty."""

    def __init__(self, message: str = "This field is required.") -> None:
        self.message = message

    def validate(self, value: Any) -> None:
        if value is None or value == "" or (
            hasattr(value, "__len__") and len(value) == 0
        ):
            raise ValidationError(self.message)


class MinLength(Validator):
    """String must be at least *n* characters."""

    def __init__(self, n: int, message: str | None = None) -> None:
        self.n = n
        self.message = message or f"Must be at least {n} characters."

    def validate(self, value: Any) -> None:
        if value is not None and len(str(value)) < self.n:
            raise ValidationError(self.message)


class MaxLength(Validator):
    """String must be at most *n* characters."""

    def __init__(self, n: int, message: str | None = None) -> None:
        self.n = n
        self.message = message or f"Must be at most {n} characters."

    def validate(self, value: Any) -> None:
        if value is not None and len(str(value)) > self.n:
            raise ValidationError(self.message)


class MinValue(Validator):
    """Numeric value must be >= *n*."""

    def __init__(self, n: int | float, message: str | None = None) -> None:
        self.n = n
        self.message = message or f"Must be at least {n}."

    def validate(self, value: Any) -> None:
        if value is not None and value < self.n:
            raise ValidationError(self.message)


class MaxValue(Validator):
    """Numeric value must be <= *n*."""

    def __init__(self, n: int | float, message: str | None = None) -> None:
        self.n = n
        self.message = message or f"Must be at most {n}."

    def validate(self, value: Any) -> None:
        if value is not None and value > self.n:
            raise ValidationError(self.message)


class EmailValidator(Validator):
    """Value must look like an email address."""

    _pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, message: str = "Enter a valid email address.") -> None:
        self.message = message

    def validate(self, value: Any) -> None:
        if value and not self._pattern.match(str(value)):
            raise ValidationError(self.message)
