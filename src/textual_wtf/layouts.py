"""Form layout classes for textual-wtf.

FieldContainer
--------------
A ``Vertical`` widget that owns the DOM for one field: label, inner input
widget, optional help text, and error display.  It is created by
``BoundField.__call__()`` and is what gets yielded in ``compose_form()``.

It handles the two messages posted by form widgets:

* ``FormValueChanged`` — updates ``BoundField._value`` directly (bypassing
  the setter to avoid a feedback loop).  Checks ``BoundField._syncing`` to
  silently ignore echoes from programmatic value sets.

* ``FormBlurred`` — triggers ``BoundField.validate()``, which in turn calls
  ``FieldContainer.update_errors()``.

FormLayout
----------
Base class for form renderers.  Subclass and override ``compose_form()``.
Handles Submit/Cancel button events and Enter/Escape keyboard shortcuts.

DefaultFormLayout
-----------------
Renders all fields in declaration order.  Used by ``Form.render()`` when no
``layout_class`` is specified.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static

from .widgets import FormBlurred, FormValueChanged
from textual_wtf import Form

if TYPE_CHECKING:
    from .bound_fields import BoundField
    from .forms import BaseForm


# ── FieldContainer ────────────────────────────────────────────────────────────

class FieldContainer(Vertical):
    """DOM container for a single form field.

    Created by ``BoundField.__call__()``.  Not instantiated directly.
    """

    DEFAULT_CSS = """
    FieldContainer {
        height: auto;
        margin-bottom: 1;
    }
    FieldContainer .field-label {
        color: $text;
    }
    FieldContainer .field-row {
        height: auto;
    }
    FieldContainer .field-help {
        color: $text-muted;
        text-style: italic;
    }
    FieldContainer .field-error {
        color: $error;
    }
    """

    def __init__(
        self,
        bound_field: BoundField,
        inner_widget: Any,
        label_style: str,
        help_style: str,
    ) -> None:
        super().__init__()
        self._bound_field = bound_field
        self._inner_widget = inner_widget
        self._label_style = label_style
        self._help_style = help_style

    def compose(self) -> ComposeResult:
        bf = self._bound_field

        # Label + widget arrangement.
        if self._label_style == "above":
            yield Label(bf.label, classes="field-label")
            yield self._inner_widget
        elif self._label_style == "beside":
            with Horizontal(classes="field-row"):
                yield Label(bf.label, classes="field-label")
                yield self._inner_widget
        else:  # "placeholder" — no Label widget; label already injected as placeholder
            yield self._inner_widget

        # Help text.
        if bf.help_text:
            if self._help_style == "below":
                yield Static(bf.help_text, classes="field-help")
            # "tooltip" handled in on_mount

        # Error display — hidden until validate() fires.
        error = Static("", classes="field-error")
        error.display = False
        yield error

    def on_mount(self) -> None:
        # Attach tooltip if help_style is "tooltip".
        if self._bound_field.help_text and self._help_style == "tooltip":
            self._inner_widget.tooltip = self._bound_field.help_text

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_form_value_changed(self, event: FormValueChanged) -> None:
        """Update BoundField._value when the user changes the widget value."""
        event.stop()
        bf = self._bound_field
        # Ignore echoes from programmatic value sets (BoundField.value setter
        # sets _syncing=True before writing to the inner widget).
        if bf._syncing:
            return
        bf._value = bf.field.to_python(event.value)
        if bf._value != bf._initial_value:
            bf.is_dirty = True

    def on_form_blurred(self, event: FormBlurred) -> None:
        """Validate the field when the inner widget loses focus."""
        event.stop()
        self._bound_field.validate()

    # ── Error display ─────────────────────────────────────────────────────────

    def update_errors(self) -> None:
        """Sync error display with ``BoundField.errors``.

        Called by ``BoundField.validate()`` after every validation pass.
        """
        try:
            error_widget = self.query_one(".field-error", Static)
            if self._bound_field.errors:
                error_widget.update(self._bound_field.errors[0])
                error_widget.display = True
            else:
                error_widget.update("")
                error_widget.display = False
        except Exception:
            pass  # not yet mounted


# ── FormLayout ────────────────────────────────────────────────────────────────

class FormLayout(VerticalScroll):
    """Base class for form renderers.

    Subclass and override :meth:`compose_form` to define the visual layout::

        class TwoColumnLayout(FormLayout):
            def compose_form(self):
                with Horizontal():
                    yield self.form.first_name()
                    yield self.form.last_name()
                yield self.form.email()
                with Horizontal(id="buttons"):
                    yield Button("Submit", id="submit", variant="primary")
                    yield Button("Cancel", id="cancel")

    Each ``BoundField`` may be yielded only once per layout; a second call
    raises ``FormError``.
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
    """

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
        """Reset BoundField render state then delegate to ``compose_form()``."""
        for bf in self.form.bound_fields.values():
            bf._rendered = False
            bf._render_label_style = None
            bf._render_help_style = None
            bf._render_disabled = None
            bf._render_extra_validators = None
            bf._render_widget_kwargs = {}
            bf._inner = None
            bf._container = None
        yield from self.compose_form()

    # ── Override in subclasses ────────────────────────────────────────────────

    def compose_form(self) -> ComposeResult:
        """Define the form's visual structure.

        Yield ``FieldContainer`` instances obtained by calling BoundFields::

            yield self.form.name()
            yield self.form.age(disabled=True)
            yield self.form.notes(label_style="above", help_style="tooltip")

        Plus any other Textual widgets needed for the layout.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement compose_form()."
        )

    # ── Submit / cancel ───────────────────────────────────────────────────────

    def _do_submit(self) -> None:
        if self.form.validate():
            self.post_message(Form.Submitted(self, self.form))

    def _do_cancel(self) -> None:
        self.post_message(Form.Cancelled(self, self.form))

    # ── Event handlers ────────────────────────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            event.stop()
            self._do_submit()
        elif event.button.id == "cancel":
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
    specified.
    """

    def compose_form(self) -> ComposeResult:
        form = self.form

        title = getattr(form, "title", None)
        if title:
            yield Static(title, id="form-title")

        for bf in form.bound_fields.values():
            yield bf()  # all defaults: field / form level label_style & help_style

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
