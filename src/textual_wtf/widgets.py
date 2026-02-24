"""Thin wrapper widgets providing a uniform interface for form fields."""

from __future__ import annotations

from typing import Any

from textual.widgets import Checkbox, Input, Select, TextArea


class FormInput(Input):
    """Wrapper around Textual Input for StringField/IntegerField."""
    pass


class FormCheckbox(Checkbox):
    """Wrapper around Textual Checkbox for BooleanField."""
    pass


class FormSelect(Select[Any]):
    pass


class FormTextArea(TextArea):
    """Wrapper around Textual TextArea for TextField."""
    pass
