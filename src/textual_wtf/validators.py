"""Built-in validators for textual-wtf.

Validators subclass textual.validation.Validator, inheriting
``success()`` and ``failure()`` methods.
"""

from __future__ import annotations

import re
from typing import Any

from textual.validation import ValidationResult
from textual.validation import Validator as TextualValidator


class Validator(TextualValidator):
    """Base class for textual-wtf validators."""

    def validate(self, value: str) -> ValidationResult:
        return self.success()


class Required(Validator):
    """Validates that a value is not None, empty string, or empty sequence."""

    def validate(self, value: str) -> ValidationResult:
        if value is None:
            return self.failure("This field is required.")
        if isinstance(value, str) and value.strip() == "":
            return self.failure("This field is required.")
        if isinstance(value, (list, tuple, set, frozenset)) and len(value) == 0:
            return self.failure("This field is required.")
        return self.success()


class MinLength(Validator):
    """Validates that len(value) >= n."""

    def __init__(self, n: int) -> None:
        super().__init__()
        self.n = n

    def validate(self, value: str) -> ValidationResult:
        if value is not None and len(value) < self.n:
            return self.failure(
                f"Ensure this value has at least {self.n} characters "
                f"(it has {len(value)})."
            )
        return self.success()


class MaxLength(Validator):
    """Validates that len(value) <= n."""

    def __init__(self, n: int) -> None:
        super().__init__()
        self.n = n

    def validate(self, value: str) -> ValidationResult:
        if value is not None and len(value) > self.n:
            return self.failure(
                f"Ensure this value has at most {self.n} characters "
                f"(it has {len(value)})."
            )
        return self.success()


class MinValue(Validator):
    """Validates that value >= n."""

    def __init__(self, n: int | float) -> None:
        super().__init__()
        self.n = n

    def validate(self, value: str) -> ValidationResult:
        if value is not None and value < self.n:
            return self.failure(
                f"Ensure this value is greater than or equal to {self.n}."
            )
        return self.success()


class MaxValue(Validator):
    """Validates that value <= n."""

    def __init__(self, n: int | float) -> None:
        super().__init__()
        self.n = n

    def validate(self, value: str) -> ValidationResult:
        if value is not None and value > self.n:
            return self.failure(
                f"Ensure this value is less than or equal to {self.n}."
            )
        return self.success()


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class EmailValidator(Validator):
    """Validates that a value matches a basic email pattern."""

    def validate(self, value: str) -> ValidationResult:
        if value is not None and isinstance(value, str) and value.strip():
            if not _EMAIL_RE.match(value):
                return self.failure("Enter a valid email address.")
        return self.success()
