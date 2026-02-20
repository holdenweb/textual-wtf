"""Textual widget wrappers for textual-wtf.

Each wrapper posts two uniform messages so that ``BoundField`` can use a
single pair of event handlers regardless of widget type:

* ``FormValueChanged(value)`` — the widget's value changed (user input).
* ``FormBlurred()``           — the widget lost focus (trigger validation).
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual.message import Message
from textual.widgets import Checkbox, Input, Select, TextArea

if TYPE_CHECKING:
    from .bound_fields import BoundField


# ── Uniform messages ─────────────────────────────────────────────────────────

class FormValueChanged(Message):
    """Posted by any form widget when its value changes (user interaction)."""

    def __init__(self, value: Any) -> None:
        super().__init__()
        self.value = value


class FormBlurred(Message):
    """Posted by any form widget when it loses focus."""


# ── Widget wrappers ──────────────────────────────────────────────────────────

class FormInput(Input):
    """Single-line text / integer input."""

    def __init__(self, *, bound_field: BoundField, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.bound_field = bound_field
        self.field = bound_field  # backward-compat alias

    def on_input_changed(self, event: Input.Changed) -> None:  # noqa: N802
        event.stop()
        self.post_message(FormValueChanged(event.value))

    def on_blur(self) -> None:
        self.post_message(FormBlurred())


class FormTextArea(TextArea):
    """Multi-line text area."""

    def __init__(self, *, bound_field: BoundField, **kwargs: Any) -> None:
        # TextArea uses 'text' not a positional value arg.
        initial_text = kwargs.pop("value", "") or ""
        super().__init__(initial_text, **kwargs)
        self.bound_field = bound_field
        self.field = bound_field

    @property
    def value(self) -> str:
        return self.text

    @value.setter
    def value(self, v: str) -> None:
        # Replace content without triggering our own changed handler.
        self._reactive_text.set(self, v or "")  # type: ignore[attr-defined]

    def on_text_area_changed(self, event: TextArea.Changed) -> None:  # noqa: N802
        event.stop()
        self.post_message(FormValueChanged(self.text))

    def on_blur(self) -> None:
        self.post_message(FormBlurred())


class FormCheckbox(Checkbox):
    """Boolean checkbox."""

    def __init__(self, *, bound_field: BoundField, **kwargs: Any) -> None:
        label = kwargs.pop("label", "")
        value = kwargs.pop("value", False)
        super().__init__(label=label, value=value, **kwargs)
        self.bound_field = bound_field
        self.field = bound_field

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:  # noqa: N802
        event.stop()
        self.post_message(FormValueChanged(event.value))

    def on_blur(self) -> None:
        self.post_message(FormBlurred())


class FormSelect(Select):
    """Choice dropdown."""

    def __init__(
        self,
        *,
        bound_field: BoundField,
        choices: list[tuple[str, Any]],
        **kwargs: Any,
    ) -> None:
        allow_blank = kwargs.pop("allow_blank", not bound_field.field.required)
        super().__init__(
            options=choices,
            allow_blank=allow_blank,
            **kwargs,
        )
        self.bound_field = bound_field
        self.field = bound_field

    def on_select_changed(self, event: Select.Changed) -> None:  # noqa: N802
        event.stop()
        value = None if event.value is Select.BLANK else event.value
        self.post_message(FormValueChanged(value))

    def on_blur(self) -> None:
        self.post_message(FormBlurred())
