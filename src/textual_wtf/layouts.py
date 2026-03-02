"""Form layout classes for rendering forms in Textual."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Label, Select, TextArea

from .field_widget import FieldWidget
from .forms import BaseForm

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .bound import BoundField


class FormLayout(VerticalScroll):
    """Base class for form renderers.

    Subclass and override compose() to create custom layouts.
    The base class handles button events and keyboard shortcuts.
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


class ControllerAwareLayout(FormLayout):
    """FormLayout mixin that routes widget events to FieldControllers.

    When a form is composed with raw inner widgets (via ``BoundField.__call__``
    rather than ``BoundField.simple_layout``), those widgets are not inside a
    ``FieldWidget`` that would handle events for them.  This mixin catches the
    relevant Textual events and routes them to the appropriate
    ``FieldController`` based on the ``._field_controller`` attribute stamped
    on each inner widget by ``BoundField.__call__``.

    Events that originate from *inside* a ``FieldWidget`` are ignored here
    (the ``FieldWidget`` handles them directly).
    """

    def _find_raw_controller(self, widget: Any) -> Any | None:
        """Return the FieldController for a raw widget not inside a FieldWidget.

        Returns ``None`` if the widget has no controller, or if it lives inside
        a ``FieldWidget`` that already handles its events.
        """
        ctrl = getattr(widget, "_field_controller", None)
        if ctrl is None:
            return None
        # Walk up the DOM; if we find a FieldWidget before reaching self,
        # the event is already handled.
        parent = widget.parent
        while parent is not None and parent is not self:
            if isinstance(parent, FieldWidget):
                return None
            parent = parent.parent
        return ctrl

    def on_input_changed(self, event: Input.Changed) -> None:
        ctrl = self._find_raw_controller(event.control)
        if ctrl is not None:
            ctrl.handle_widget_input(event.value, "change")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        ctrl = self._find_raw_controller(event.control)
        if ctrl is not None:
            ctrl.handle_widget_input(event.value, "change")

    def on_select_changed(self, event: Select.Changed) -> None:
        ctrl = self._find_raw_controller(event.control)
        if ctrl is not None:
            value = event.value if event.value is not Select.BLANK else None
            ctrl.handle_widget_input(value, "change")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        ctrl = self._find_raw_controller(event.control)
        if ctrl is not None:
            ctrl.handle_widget_input(event.control.text, "change")

    def on_descendant_blur(self, event: Any) -> None:
        ctrl = self._find_raw_controller(event.widget)
        if ctrl is not None:
            ctrl.validate_for("blur")


class DefaultFormLayout(ControllerAwareLayout):
    """Renders all fields in declaration order with default styling.

    Adds a title bar (if the form has a title) and Submit/Cancel buttons.
    Each field is rendered via ``BoundField.simple_layout()``.
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
            if not bf.controller.is_consumed:
                yield bf.simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
