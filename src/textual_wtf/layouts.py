"""Form layout classes for rendering forms in Textual."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Label

from .forms import BaseForm

if TYPE_CHECKING:
    from textual.app import ComposeResult


class FormLayout(VerticalScroll):
    """Base class for form renderers.

    Subclass and override compose() to create custom layouts.
    The base class handles button events, keyboard shortcuts,
    and duplicate-field protection.
    """

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    FormLayout {
        height: auto;
        max-height: 100%;
    }
    FormLayout #buttons {
        height: auto;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        form: BaseForm,
        id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.form = form

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            self._do_submit()
        elif event.button.id == "cancel":
            self._do_cancel()

    def action_submit(self) -> None:
        self._do_submit()

    def action_cancel(self) -> None:
        self._do_cancel()

    def _do_submit(self) -> None:
        """Run the full clean pipeline; post Submitted only if valid."""
        if self.form.clean():
            self.post_message(
                BaseForm.Submitted(layout=self, form=self.form)
            )

    def _do_cancel(self) -> None:
        self.post_message(
            BaseForm.Cancelled(layout=self, form=self.form)
        )


class DefaultFormLayout(FormLayout):
    """Renders all fields in declaration order with default styling.

    Adds a title bar (if the form has a title) and Submit/Cancel buttons.
    """

    DEFAULT_CSS = """
    DefaultFormLayout {
        height: auto;
        max-height: 100%;
        padding: 1 2;
    }
    DefaultFormLayout .form-title {
        text-style: bold;
        margin-bottom: 1;
    }
    DefaultFormLayout #buttons {
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        title = getattr(self.form, "title", "")
        if title:
            yield Label(title, classes="form-title")

        for _name, bf in self.form.bound_fields.items():
            if not bf._rendered:
                bf._mark_rendered()
            yield bf

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
