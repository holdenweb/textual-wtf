"""FieldWidget — Textual Container that renders a single field with chrome."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from .types import HelpStyle, LabelStyle

from textual import events
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Checkbox, Input, Label, Select, Static, TextArea

from .field_errors import FieldErrors
from .widgets import FormCheckbox, FormInput, FormSelect, FormTextArea

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .bound import BoundField


class FieldWidget(Container):
    """Textual Container that renders a BoundField as label + input + help + error.

    Returned by ``BoundField.simple_layout()``.  Connects to the field's
    :class:`~textual_wtf.FieldController` via listeners so that:

    * Widget events (typing, blur, …) are forwarded to the controller.
    * Programmatic changes (``bf.value = x``, form-level ``add_error``)
      are reflected in the UI automatically.

    Pass a ``renderer`` callable to ``BoundField.simple_layout(renderer=…)``
    to override the entire compose subtree.  The callable receives the
    ``BoundField`` and must return a ``ComposeResult``.
    """

    DEFAULT_CSS = """
    FieldWidget {
        height: auto;
        margin-bottom: 1;
    }
    FieldWidget .field-beside {
        height: auto;
    }
    FieldWidget .field-input-col {
        height: auto;
        width: 1fr;
    }
    FieldWidget .field-label {
        margin-bottom: 0;
    }
    FieldWidget .field-help {
        color: $text-muted;
        margin-top: 0;
        padding-left: 1;
    }
    FieldWidget Input,
    FieldWidget Select,
    FieldWidget TextArea {
        background: $boost;
    }
    """

    # 'value' reactive is used exclusively to push programmatic value changes
    # into the inner widget (watch_value).  Widget-event paths update the
    # controller directly and never touch this reactive to avoid loops.
    _external_value: reactive[Any] = reactive(None, init=False)

    def __init__(
        self,
        bound_field: BoundField,
        *,
        label_style: LabelStyle,
        help_style: HelpStyle,
        disabled: bool,
        widget_kwargs: dict[str, Any],
        renderer: Callable[[BoundField], ComposeResult] | None = None,
    ) -> None:
        super().__init__()
        self.bound_field = bound_field
        self._label_style = label_style
        self._help_style = help_style
        self._disabled = disabled
        self._widget_kwargs = widget_kwargs
        self._renderer = renderer
        self._inner_widget: Widget | None = None

        ctrl = bound_field.controller
        # Set initial reactive state without triggering watchers
        self.set_reactive(FieldWidget._external_value, ctrl.value)

        # Register with the controller so that external value changes propagate here
        ctrl.add_value_listener(self._on_external_value_change)

    # ── Controller callbacks ──────────────────────────────────────

    def _on_external_value_change(self, new_value: Any) -> None:
        """Called by controller when the value is set from outside (e.g. set_data)."""
        self._external_value = new_value

    # ── Textual compose ───────────────────────────────────────────

    def compose(self) -> ComposeResult:
        bf = self.bound_field

        if self._renderer is not None:
            yield from self._renderer(bf)
            return

        self._inner_widget = inner_widget = bf._build_inner_widget(
            disabled=self._disabled,
            widget_kwargs=self._widget_kwargs,
        )
        # Stamp the controller for ControllerAwareLayout ancestors
        inner_widget._field_controller = bf.controller  # type: ignore[attr-defined]

        ls = self._label_style
        hs = self._help_style

        if ls == "above":
            yield Label(bf.label, classes="field-label")
            with Vertical(classes="field-input-col"):
                yield inner_widget
                if bf.help_text and hs == "below":
                    yield Static(bf.help_text, classes="field-help")
                elif bf.help_text and hs == "tooltip":
                    inner_widget.tooltip = bf.help_text
                yield FieldErrors(bf.controller)

        elif ls == "beside":
            with Horizontal(classes="field-beside"):
                yield Label(bf.label, classes="field-label")
                with Vertical(classes="field-input-col"):
                    yield inner_widget
                    if bf.help_text and hs == "below":
                        yield Static(bf.help_text, classes="field-help")
                    elif bf.help_text and hs == "tooltip":
                        inner_widget.tooltip = bf.help_text
                    yield FieldErrors(bf.controller)

        elif ls == "placeholder":
            if isinstance(inner_widget, (Input, FormInput)):
                inner_widget.placeholder = bf.label
            with Vertical(classes="field-input-col"):
                yield inner_widget
                if bf.help_text and hs == "below":
                    yield Static(bf.help_text, classes="field-help")
                elif bf.help_text and hs == "tooltip":
                    inner_widget.tooltip = bf.help_text
                yield FieldErrors(bf.controller)

    # ── Reactive watchers ─────────────────────────────────────────

    def watch__external_value(self, new_value: Any) -> None:
        """Sync a programmatic value change into the inner widget."""
        if self._inner_widget is None:
            return
        try:
            w = self._inner_widget
            if isinstance(w, (Checkbox, FormCheckbox)):
                w.value = bool(new_value)
            elif isinstance(w, (Select, FormSelect)):
                w.value = new_value if new_value is not None else Select.BLANK
            elif isinstance(w, (TextArea, FormTextArea)):
                w.text = str(new_value) if new_value is not None else ""
            elif isinstance(w, (Input, FormInput)):
                w.value = str(new_value) if new_value is not None else ""
        except Exception:
            pass

    # ── Widget event handlers ─────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if not isinstance(self._inner_widget, (Input, FormInput)):
            return
        ctrl = self.bound_field.controller
        had_error = ctrl.has_error
        ctrl.handle_widget_input(event.value, "change")
        # If errors cleared on change but the field previously had a stale blur
        # error, run blur validators now so the error dismisses immediately.
        if not ctrl.has_error and had_error:
            ctrl.validate_for("blur")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        ctrl = self.bound_field.controller
        ctrl.handle_widget_input(event.value, "change")

    def on_select_changed(self, event: Select.Changed) -> None:
        ctrl = self.bound_field.controller
        value = event.value if event.value is not Select.BLANK else None
        ctrl.handle_widget_input(value, "change")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if not isinstance(self._inner_widget, (TextArea, FormTextArea)):
            return
        ctrl = self.bound_field.controller
        ctrl.handle_widget_input(self._inner_widget.text, "change")

    def on_descendant_blur(self, event: events.DescendantBlur) -> None:
        if event.widget is self._inner_widget:
            ctrl = self.bound_field.controller
            ctrl.validate_for("blur")   # notifies listeners (e.g. TabbedForm tab state)
