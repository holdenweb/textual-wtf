"""FieldErrors — label widget that auto-displays a field's current errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Label

if TYPE_CHECKING:
    from .controller import FieldController


class FieldErrors(Label):
    """A label that subscribes to a :class:`~textual_wtf.FieldController` and
    displays its current error messages, hiding itself when the field is valid.

    Use this alongside a raw ``bf()`` widget when building custom layouts that
    don't use :meth:`~textual_wtf.BoundField.simple_layout`::

        yield Label(bf.field.label)
        yield bf()
        yield FieldErrors(bf.controller)

    The widget registers itself with the controller on mount and automatically
    updates whenever the error state changes.  It deregisters itself on unmount,
    so its lifetime is independent of the controller's.

    ``FieldWidget`` uses ``FieldErrors`` internally for its own error display,
    so both code paths share the same mechanism.
    """

    DEFAULT_CSS = """
    FieldErrors {
        color: $error;
        display: none;
        height: auto;
        width: 1fr;
        margin-top: 0;
        padding-left: 1;
    }
    FieldErrors.has-error {
        display: block;
    }
    """

    def __init__(self, controller: FieldController) -> None:
        # Keep the `field-error` class so external CSS selectors and tests
        # that target `.field-error` continue to work.
        super().__init__("", classes="field-error")
        self._controller = controller

    def on_mount(self) -> None:
        self._controller.add_error_listener(self._update)
        # Sync to whatever state the controller already holds.
        self._update(self._controller.has_error, list(self._controller.error_messages))

    def on_unmount(self) -> None:
        self._controller.remove_error_listener(self._update)

    def _update(self, has_error: bool, messages: list[str]) -> None:
        if has_error:
            self.add_class("has-error")
            self.update("\n".join(messages))
        else:
            self.remove_class("has-error")
            self.update("")
