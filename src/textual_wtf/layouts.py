"""Form layout classes for textual-wtf.

``FormLayout`` is a ``VerticalScroll`` whose ``compose()`` delegates to
``compose_form()``.  Subclass it and override ``compose_form()`` to create
custom form presentations::

    class TwoColumnLayout(FormLayout):
        def compose_form(self):
            with Horizontal():
                yield self.form.first_name()
                yield self.form.last_name()
            yield self.form.email()
            with Horizontal(id="buttons"):
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Cancel", id="cancel")

``DefaultFormLayout`` replicates the classic stacked-field presentation with
Submit and Cancel buttons added automatically.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Static

from .bound_fields import BoundField
from .exceptions import FormError

if TYPE_CHECKING:
    from .forms import BaseForm


class FormLayout(VerticalScroll):
    """Base class for form renderers.

    Handles ``Form.Submitted`` / ``Form.Cancelled`` messages, Submit/Cancel
    button events, and Enter / Escape keyboard shortcuts.

    Subclass and override :meth:`compose_form` to define the visual layout.
    Do **not** override :meth:`compose` directly.
    """

    DEFAULT_CSS = """
    FormLayout {
        keyline: thin $primary;
    }
    FormLayout #form-title {
        background: $primary;
        color: $text;
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    FormLayout #buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    FormLayout .form-error-summary {
        color: $error;
        height: auto;
        margin-top: 1;
    }
    """

    # ── Messages ──────────────────────────────────────────────────────────────

    class Submitted(Message):
        """Posted when the user submits the form (all fields valid)."""

        def __init__(self, layout: FormLayout, form: BaseForm) -> None:
            super().__init__()
            self.layout = layout
            self.form = form  # convenience alias

    class Cancelled(Message):
        """Posted when the user cancels the form."""

        def __init__(self, layout: FormLayout, form: BaseForm) -> None:
            super().__init__()
            self.layout = layout
            self.form = form

    # ── Construction ──────────────────────────────────────────────────────────

    def __init__(
        self,
        form: BaseForm,
        id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.form = form

    # ── Core compose entry point ──────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        """Reset render state then delegate to ``compose_form()``."""
        for bf in self.form.bound_fields.values():
            bf._rendered = False
            bf._render_label_style = None
            bf._render_help_style = None
            bf._render_disabled = None
            bf._render_extra_validators = None
            bf._render_widget_kwargs = {}
        yield from self.compose_form()

    # ── Override in subclasses ────────────────────────────────────────────────

    def compose_form(self) -> ComposeResult:
        """Define the form's visual structure.

        Yield ``BoundField`` instances via the callable interface::

            yield self.form.name()
            yield self.form.age(disabled=True)
            yield self.form.notes(label_style="above", help_style="tooltip")

        Plus any other Textual widgets (buttons, containers, labels) needed.

        Each ``BoundField`` may only be yielded once; a second yield raises
        ``FormError``.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement compose_form()."
        )

    # ── Submit / cancel helpers ───────────────────────────────────────────────

    def _do_submit(self) -> None:
        if self.form.validate():
            self.post_message(self.Submitted(self, self.form))

    def _do_cancel(self) -> None:
        self.post_message(self.Cancelled(self, self.form))

    # ── Event handlers ────────────────────────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "submit":
            event.stop()
            self._do_submit()
        elif button_id == "cancel":
            event.stop()
            self._do_cancel()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            event.stop()
            self._do_submit()
        elif event.key == "escape":
            event.stop()
            self._do_cancel()


# ── DefaultFormLayout ─────────────────────────────────────────────────────────

class DefaultFormLayout(FormLayout):
    """Renders all fields in declaration order with Submit and Cancel buttons.

    Used automatically by ``Form.render()`` when no ``layout_class`` is
    specified.  Equivalent to the old ``RenderedForm`` behaviour.
    """

    def compose_form(self) -> ComposeResult:
        form = self.form

        # Optional form title.
        title = getattr(form, "title", None)
        if title:
            yield Static(title, id="form-title")

        # All fields in declaration order.
        for bf in form.bound_fields.values():
            yield bf()  # call with no overrides → use field / form defaults

        # Buttons.
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
