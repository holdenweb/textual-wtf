"""BoundField — mutable runtime state for one field within one form instance.

Also a Textual Container widget that composes the label, inner input
widget, help text, and error display.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Checkbox, Input, Label, Select, Static, TextArea

from .exceptions import FormError, ValidationError
from .types import HelpStyle, LabelStyle
from .validators import FunctionValidator, Required, Validator
from .widgets import FormCheckbox, FormInput, FormSelect, FormTextArea

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .fields import Field
    from .forms import BaseForm


class BoundField(Container):
    """Mutable runtime state for one field within one form instance.

    Created by Field.bind() during BaseForm.__init__(). Not instantiated
    directly.
    """

    DEFAULT_CSS = """
    BoundField {
        height: auto;
        margin-bottom: 1;
    }
    BoundField .field-beside {
        height: auto;
    }
    BoundField .field-input-col {
        height: auto;
        width: 1fr;
    }
    BoundField .field-label {
        margin-bottom: 0;
    }
    BoundField .field-help {
        color: $text-muted;
        margin-top: 0;
    }
    BoundField .field-error {
        color: $error;
        display: none;
        margin-top: 0;
    }
    BoundField .field-error.has-error {
        display: block;
    }
    """

    value: reactive[Any] = reactive(None, init=False)
    has_error: reactive[bool] = reactive(False)
    error_messages: reactive[list[str]] = reactive(list, init=False)

    def __init__(
        self,
        field: Field,
        form: BaseForm,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self._field = field
        self._form = form
        self._name = name
        self._rendered = False

        # Mutable per-instance state
        self.disabled = field.disabled
        self.errors: list[str] = []
        self.is_dirty = False

        # Style overrides (can be changed via __call__)
        self._label_style: LabelStyle = field.label_style
        self._help_style: HelpStyle = field.help_style

        # Widget kwargs accumulated from Field + __call__
        self._widget_kwargs: dict[str, Any] = dict(field.widget_kwargs)

        # Initial value: data dict takes precedence over field default.
        # Apply to_python() immediately so the programmer always sees a
        # correctly-typed value; fall back to the raw value on error so
        # that validate() can still surface the coercion failure later.
        data = data or {}
        raw = data[name] if name in data else field.initial
        try:
            self._initial = field.to_python(raw)
        except ValidationError:
            self._initial = raw

        # Set reactive values without triggering watchers
        self.set_reactive(BoundField.value, self._initial)
        self.set_reactive(BoundField.error_messages, [])

        # Inner widget reference (populated during compose)
        self._inner_widget: Widget | None = None

    # ── Properties delegated to Field (read-only) ───────────────

    @property
    def field(self) -> Field:
        return self._field

    @property
    def form(self) -> BaseForm:
        return self._form

    @property
    def name(self) -> str:
        return self._name

    @property
    def label(self) -> str:
        return self._field.label

    @property
    def default(self) -> Any:
        return self._field.initial

    @property
    def required(self) -> bool:
        return self._field.required

    @property
    def help_text(self) -> str:
        return self._field.help_text

    @property
    def label_style(self) -> LabelStyle:
        return self._label_style

    @property
    def help_style(self) -> HelpStyle:
        return self._help_style

    @property
    def validators(self) -> list:
        return self._field.validators

    # ── __call__ — configure for rendering ──────────────────────

    def __call__(
        self,
        *,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        disabled: bool | None = None,
        validators: list | None = None,
        **widget_kwargs: Any,
    ) -> BoundField:
        """Configure this BoundField for rendering and return self.

        Any keyword argument here takes precedence over the Field
        declaration. widget_kwargs merge with (and override) existing ones.
        """
        if self._rendered:
            raise FormError(
                f"Field {self._name!r} has already been yielded in this layout."
            )
        self._rendered = True

        if label_style is not None:
            self._label_style = label_style
        if help_style is not None:
            self._help_style = help_style
        if disabled is not None:
            self.disabled = disabled
        if validators is not None:
            self._field.validators = [
                v if isinstance(v, Validator) else FunctionValidator(v)
                for v in validators
            ]

        self._widget_kwargs.update(widget_kwargs)
        return self

    # ── Validation ──────────────────────────────────────────────

    def validate(self) -> bool:
        """Validate this field's current value.

        Runs to_python for type coercion, checks required, then runs
        all field-level validators (success/failure pattern). Updates
        errors, error_messages, and has_error. Returns True if valid.
        """
        self.errors = []
        failures: list[str] = []

        # 1. Type coercion via to_python
        try:
            python_value = self._field.to_python(self.value)
        except ValidationError as e:
            failures.append(e.message)
            self.errors = failures
            self.has_error = True
            self.error_messages = failures
            return False

        # Store the coerced value back
        self.value = python_value

        # 2. Required check
        if self._field.required:
            result = Required().validate(python_value)
            if not result.is_valid:
                desc = (
                    result.failure_descriptions[0]
                    if result.failure_descriptions
                    else "This field is required."
                )
                failures.append(desc)
                self.errors = failures
                self.has_error = True
                self.error_messages = failures
                return False

        # 3. Skip further validation if empty and not required
        is_empty = (
            python_value is None
            or (isinstance(python_value, str) and python_value.strip() == "")
        )
        if is_empty:
            self.errors = []
            self.has_error = False
            self.error_messages = []
            return True

        # 4. Run all field validators (all are Validator instances after
        #    normalisation in Field.__init__ / BoundField.__call__)
        for v in self._field.validators:
            result = v.validate(python_value)
            if not result.is_valid:
                for desc in result.failure_descriptions:
                    failures.append(desc)

        if failures:
            self.errors = failures
            self.has_error = True
            self.error_messages = failures
            return False

        self.errors = []
        self.has_error = False
        self.error_messages = []
        return True

    # ── Textual compose ─────────────────────────────────────────

    def compose(self) -> ComposeResult:
        """Yield the field's widget subtree based on label_style and help_style."""
        inner_widget = self._build_inner_widget()
        self._inner_widget = inner_widget

        ls = self._label_style
        hs = self._help_style

        if ls == "above":
            yield Label(self.label, classes="field-label")
            with Vertical(classes="field-input-col"):
                yield inner_widget
                if self.help_text:
                    if hs == "below":
                        yield Static(self.help_text, classes="field-help")
                    elif hs == "tooltip":
                        inner_widget.tooltip = self.help_text
                yield Label("", classes="field-error")
        elif ls == "beside":
            with Horizontal(classes="field-beside"):
                yield Label(self.label, classes="field-label")
                with Vertical(classes="field-input-col"):
                    yield inner_widget
                    if self.help_text:
                        if hs == "below":
                            yield Static(self.help_text, classes="field-help")
                        elif hs == "tooltip":
                            inner_widget.tooltip = self.help_text
                    yield Label("", classes="field-error")
        elif ls == "placeholder":
            if isinstance(inner_widget, (Input, FormInput)):
                inner_widget.placeholder = self.label
            with Vertical(classes="field-input-col"):
                yield inner_widget
                if self.help_text:
                    if hs == "below":
                        yield Static(self.help_text, classes="field-help")
                    elif hs == "tooltip":
                        inner_widget.tooltip = self.help_text
                yield Label("", classes="field-error")

    def _build_inner_widget(self) -> Widget:
        """Instantiate the inner widget from Field configuration."""
        from .fields import BooleanField, ChoiceField

        widget_class = self._field.widget_class
        kwargs = dict(self._widget_kwargs)

        if isinstance(self._field, BooleanField):
            widget = widget_class(self.label, self.value or False, **kwargs)
        elif isinstance(self._field, ChoiceField):
            options = [(lbl, val) for lbl, val in self._field.choices]
            legal_values = {val for _, val in self._field.choices}
            if self.value in legal_values:
                widget = widget_class(options, value=self.value, **kwargs)
            else:
                widget = widget_class(options, allow_blank=True, **kwargs)
        elif widget_class in (FormTextArea, TextArea):
            widget = widget_class(**kwargs)
            val = self.value
            widget.text = str(val) if val is not None else ""
        else:
            # Input-like widgets
            val = self.value
            widget = widget_class(
                value=str(val) if val is not None else "",
                **kwargs,
            )

        widget.disabled = self.disabled
        return widget

    # ── Reactive watchers ───────────────────────────────────────

    def watch_value(self, new_value: Any) -> None:
        """Sync programmatic value changes to the inner widget."""
        if self._inner_widget is None:
            return
        try:
            if isinstance(self._inner_widget, (Checkbox, FormCheckbox)):
                self._inner_widget.value = bool(new_value)
            elif isinstance(self._inner_widget, (Select, FormSelect)):
                self._inner_widget.value = (
                    new_value if new_value is not None else Select.BLANK
                )
            elif isinstance(self._inner_widget, (TextArea, FormTextArea)):
                self._inner_widget.text = (
                    str(new_value) if new_value is not None else ""
                )
            elif isinstance(self._inner_widget, (Input, FormInput)):
                self._inner_widget.value = (
                    str(new_value) if new_value is not None else ""
                )
        except Exception:
            pass

    def watch_has_error(self, has_error: bool) -> None:
        """Toggle error label visibility."""
        try:
            error_label = self.query_one(".field-error", Label)
            if has_error:
                error_label.add_class("has-error")
            else:
                error_label.remove_class("has-error")
        except NoMatches:
            pass

    def watch_error_messages(self, messages: list[str]) -> None:
        """Update error label text."""
        try:
            error_label = self.query_one(".field-error", Label)
            error_label.update("\n".join(messages))
        except NoMatches:
            pass

    # ── Event handlers ──────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        """Sync Input widget value back to BoundField."""
        if isinstance(self._inner_widget, (Input, FormInput)):
            try:
                self.value = self._field.to_python(event.value)
            except ValidationError:
                self.value = event.value
            self.is_dirty = True

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Sync Checkbox value back to BoundField."""
        self.value = event.value
        self.is_dirty = True

    def on_select_changed(self, event: Select.Changed) -> None:
        """Sync Select value back to BoundField."""
        self.value = event.value
        self.is_dirty = True

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Sync TextArea value back to BoundField."""
        if isinstance(self._inner_widget, (TextArea, FormTextArea)):
            self.value = self._inner_widget.text
            self.is_dirty = True

    def on_blur(self) -> None:
        """Validate on blur."""
        self.validate()

    # ── Internal helpers ────────────────────────────────────────

    def _mark_rendered(self) -> None:
        """Mark as rendered (for duplicate detection by DefaultFormLayout)."""
        if self._rendered:
            raise FormError(
                f"Field {self._name!r} has already been yielded in this layout."
            )
        self._rendered = True
