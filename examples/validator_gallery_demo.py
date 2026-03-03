"""
Validator gallery: one field per validator type, all in a single form.

Field         Validator(s)
─────────────────────────────────────────────────────────────────────────────
required      Required           — added automatically by required=True
username      MinLength(3)       — fires on blur and submit
              + MaxLength(15)    — fires live as you type (validate_on=change)
score         MinValue(0)        — fires on blur and submit
              + MaxValue(100)    — fires live as you type (via IntegerField)
email         EmailValidator     — fires on blur and submit
slug          FunctionValidator  — plain function wrapped automatically by Field
password      StrongPassword     — custom Validator subclass + MinLength(8)
─────────────────────────────────────────────────────────────────────────────

Key points:

- MaxLength and MaxValue fire immediately as you type because their
  ``validate_on`` frozenset includes ``"change"`` (as well as ``"blur"``
  and ``"submit"``).  All other validators only fire on blur and submit.

- A plain function passed in the ``validators=`` list is automatically wrapped
  in ``FunctionValidator``.  Raise ``ValidationError`` from the function to
  signal failure; return normally to signal success.

- Subclassing ``Validator`` gives you full control over ``validate_on`` and
  lets you carry configuration as instance attributes.

Run with: python -m examples  (select "Validator Gallery")
"""

from __future__ import annotations

import re
from typing import Any

from textual.app import ComposeResult, on
from textual.validation import ValidationResult

from textual_wtf import (
    EmailValidator,
    Form,
    IntegerField,
    StringField,
    ValidationError,
    Validator,
)

from .example_screen import ExampleScreen


# ── Custom Validator subclass ─────────────────────────────────────────────────


class StrongPassword(Validator):
    """Requires at least one digit and one uppercase letter.

    Subclassing ``Validator`` is the right choice when you need reusable,
    testable validation logic that carries configuration or relies on
    ``validate_on`` control that a plain lambda cannot express.
    """

    def validate(self, value: Any) -> ValidationResult:
        if value:
            if not any(c.isdigit() for c in value):
                return self.failure("Must contain at least one digit.")
            if not any(c.isupper() for c in value):
                return self.failure("Must contain at least one uppercase letter.")
        return self.success()


# ── FunctionValidator source (plain function) ─────────────────────────────────


def must_be_slug(value: str | None) -> None:
    """Raise ValidationError if value is not a valid URL slug.

    Field automatically wraps this function in FunctionValidator when it
    appears in the ``validators=`` list.  Raise ``ValidationError`` to fail;
    return normally (or return ``None``) to succeed.
    """
    if value and not re.match(r"^[a-z0-9-]+$", value):
        raise ValidationError("Use only lowercase letters, digits, and hyphens.")


# ── Gallery form ──────────────────────────────────────────────────────────────


class ValidatorGalleryForm(Form):
    """Six fields, six validator patterns, each explained in help_text."""

    title = "Validator Gallery"
    label_style = "above"
    help_style = "below"

    required_field = StringField(
        "Required field",
        required=True,
        help_text=(
            "Required — field cannot be empty; "
            "fires on blur and submit"
        ),
    )
    username = StringField(
        "Username",
        min_length=3,
        max_length=15,
        help_text=(
            "MinLength(3) fires on blur / submit; "
            "MaxLength(15) fires live as you type"
        ),
    )
    score = IntegerField(
        "Score",
        minimum=0,
        maximum=100,
        help_text=(
            "MinValue(0) fires on blur / submit; "
            "MaxValue(100) fires live as you type"
        ),
    )
    email = StringField(
        "Email",
        validators=[EmailValidator()],
        help_text="EmailValidator — checks a basic email pattern on blur / submit",
    )
    slug = StringField(
        "URL slug",
        validators=[must_be_slug],
        help_text=(
            "FunctionValidator (plain function) — "
            "only lowercase letters, digits, and hyphens"
        ),
    )
    password = StringField(
        "Password",
        min_length=8,
        validators=[StrongPassword()],
        help_text=(
            "Custom Validator subclass (StrongPassword) + MinLength(8); "
            "needs a digit and an uppercase letter"
        ),
    )


# ── Demo screen ───────────────────────────────────────────────────────────────


class ValidatorGalleryDemoScreen(ExampleScreen):
    """Validator gallery rendered with form.layout() — no compose code needed."""

    CSS = """
    ValidatorGalleryDemoScreen { align: center middle; }

    DefaultFormLayout {
        width: 72;
        max-height: 90%;
        border: double $primary;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = ValidatorGalleryForm()
        yield self.form.layout()

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"All valid!  {data}", severity="information", timeout=8)

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Cancelled", severity="warning")
        self.action_back()
