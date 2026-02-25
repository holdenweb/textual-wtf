"""Built-in validators for textual-wtf.

Validators subclass textual.validation.Validator, inheriting
``success()`` and ``failure()`` methods.

Each validator carries a ``validate_on`` frozenset that controls which
*interactive* events trigger it automatically.  The submit path
(``BoundField.validate()``) always runs every validator regardless.

Default event assignments:

* ``{"blur", "submit"}``   — Required, MinLength, MinValue, EmailValidator,
                    FunctionValidator (fire when leaving the field and on submit)
* ``{"change", "blur", "submit"}`` — MaxLength, MaxValue
                    (fire immediately while typing, on blur, and on submit)

Override per-class by setting ``validate_on`` as a class attribute, or
per-instance by passing ``validate_on=`` at construction time.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from textual.validation import ValidationResult
from textual.validation import Validator as TextualValidator

from .exceptions import ValidationError


class Validator(TextualValidator):
    """Base class for textual-wtf validators.

    Fires on ``{"blur", "submit"}`` by default.
    """

    validate_on: frozenset[str] = frozenset({"blur", "submit"})

    def __init__(
        self,
        failure_description: str | None = None,
        *,
        validate_on: frozenset[str] | None = None,
    ) -> None:
        super().__init__(failure_description)
        if validate_on is not None:
            self.validate_on = frozenset(validate_on)

    def validate(self, value: Any) -> ValidationResult:
        return self.success()


class FunctionValidator(Validator):
    """Adapt a plain callable into the Validator interface.

    The callable receives the field value and should either return
    normally (indicating success) or raise ``ValidationError`` with a
    descriptive message (indicating failure).

    Example::

        def no_spaces(value):
            if " " in value:
                raise ValidationError("No spaces allowed.")

        name = StringField("Name", validators=[no_spaces])
    """

    def __init__(
        self,
        fn: Callable[[Any], None],
        *,
        validate_on: frozenset[str] | None = None,
    ) -> None:
        super().__init__(validate_on=validate_on)
        self._fn = fn

    def validate(self, value: Any) -> ValidationResult:
        try:
            self._fn(value)
            return self.success()
        except ValidationError as e:
            return self.failure(e.message)


class Required(Validator):
    """Validates that a value is not None, empty string, or empty sequence."""

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return self.failure("This field is required.")
        if isinstance(value, str) and value.strip() == "":
            return self.failure("This field is required.")
        if isinstance(value, (list, tuple, set, frozenset)) and len(value) == 0:
            return self.failure("This field is required.")
        return self.success()


class MinLength(Validator):
    """Validates that len(value) >= n."""

    def __init__(self, n: int, *, validate_on: frozenset[str] | None = None) -> None:
        super().__init__(validate_on=validate_on)
        self.n = n

    def validate(self, value: Any) -> ValidationResult:
        if value is not None and len(value) < self.n:
            return self.failure(
                f"Ensure this value has at least {self.n} characters "
                f"(it has {len(value)})."
            )
        return self.success()


class MaxLength(Validator):
    """Validates that len(value) <= n.

    Fires on ``{"change", "blur", "submit"}`` by default so the limit is
    enforced immediately as the user types.
    """

    validate_on: frozenset[str] = frozenset({"change", "blur", "submit"})

    def __init__(self, n: int, *, validate_on: frozenset[str] | None = None) -> None:
        super().__init__(validate_on=validate_on)
        self.n = n

    def validate(self, value: Any) -> ValidationResult:
        if value is not None and len(value) > self.n:
            return self.failure(
                f"Ensure this value has at most {self.n} characters "
                f"(it has {len(value)})."
            )
        return self.success()


class MinValue(Validator):
    """Validates that value >= n."""

    def __init__(
        self, n: int | float, *, validate_on: frozenset[str] | None = None
    ) -> None:
        super().__init__(validate_on=validate_on)
        self.n = n

    def validate(self, value: Any) -> ValidationResult:
        if value is not None and value < self.n:
            return self.failure(
                f"Ensure this value is greater than or equal to {self.n}."
            )
        return self.success()


class MaxValue(Validator):
    """Validates that value <= n.

    Fires on ``{"change", "blur", "submit"}`` by default so the limit is
    enforced immediately as the user types.
    """

    validate_on: frozenset[str] = frozenset({"change", "blur", "submit"})

    def __init__(
        self, n: int | float, *, validate_on: frozenset[str] | None = None
    ) -> None:
        super().__init__(validate_on=validate_on)
        self.n = n

    def validate(self, value: Any) -> ValidationResult:
        if value is not None and value > self.n:
            return self.failure(
                f"Ensure this value is less than or equal to {self.n}."
            )
        return self.success()


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class EmailValidator(Validator):
    """Validates that a value matches a basic email pattern."""

    def validate(self, value: Any) -> ValidationResult:
        if value is not None and isinstance(value, str) and value.strip():
            if not _EMAIL_RE.match(value):
                return self.failure("Enter a valid email address.")
        return self.success()
