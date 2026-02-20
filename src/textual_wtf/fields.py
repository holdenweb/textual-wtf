"""Field classes for textual-wtf.

Fields are immutable declarative configuration objects defined at class level
on a ``Form`` subclass.  They never hold runtime state; all mutable state
lives in ``BoundField`` instances created by ``Field.bind()``.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .exceptions import FieldError, ValidationError
from .validators import MinValue as MinValueValidator, MaxValue as MaxValueValidator, Validator

if TYPE_CHECKING:
    from .bound_fields import BoundField
    from .forms import BaseForm

# Sentinel — distinguishes "user explicitly set this" from "using built-in default".
# Allows Form-level label_style / help_style defaults to be overridden correctly.
_UNSET: object = object()

LabelStyle = str  # Literal["above", "beside", "placeholder"]
HelpStyle = str   # Literal["below", "tooltip"]

_VALID_LABEL_STYLES = {"above", "beside", "placeholder"}
_VALID_HELP_STYLES = {"below", "tooltip"}


class Field:
    """Immutable declarative configuration for a single form field."""

    def __init__(
        self,
        label: str,
        *,
        initial: Any = None,
        required: bool = False,
        disabled: bool = False,
        validators: list = (),
        help_text: str = "",
        label_style: LabelStyle | object = _UNSET,
        help_style: HelpStyle | object = _UNSET,
        widget_class: type | None = None,
        **widget_kwargs: Any,
    ) -> None:
        if label_style is not _UNSET and label_style not in _VALID_LABEL_STYLES:
            raise FieldError(
                f"Invalid label_style {label_style!r}. "
                f"Choose from: {sorted(_VALID_LABEL_STYLES)}"
            )
        if help_style is not _UNSET and help_style not in _VALID_HELP_STYLES:
            raise FieldError(
                f"Invalid help_style {help_style!r}. "
                f"Choose from: {sorted(_VALID_HELP_STYLES)}"
            )

        self.label = label
        self.initial = initial
        self.required = required
        self.disabled = disabled
        self.validators: list = list(validators)
        self.help_text = help_text
        self._label_style: LabelStyle | object = label_style  # may be _UNSET
        self._help_style: HelpStyle | object = help_style     # may be _UNSET
        self._widget_class = widget_class
        self.widget_kwargs: dict[str, Any] = widget_kwargs

    # ── Resolved style properties ────────────────────────────────────────────

    @property
    def label_style(self) -> LabelStyle:
        return "above" if self._label_style is _UNSET else self._label_style  # type: ignore[return-value]

    @property
    def help_style(self) -> HelpStyle:
        return "below" if self._help_style is _UNSET else self._help_style  # type: ignore[return-value]

    # ── Widget class (resolved lazily in subclasses) ──────────────────────────

    @property
    def widget_class(self) -> type:
        if self._widget_class is not None:
            return self._widget_class
        return self._default_widget_class()

    def _default_widget_class(self) -> type:
        """Return the default widget class. Overridden in subclasses."""
        from .widgets import FormInput
        return FormInput

    # ── Binding ───────────────────────────────────────────────────────────────

    def bind(
        self,
        form: BaseForm,
        name: str,
        initial: Any = None,
    ) -> BoundField:
        """Create a ``BoundField`` for this field within *form*."""
        from .bound_fields import BoundField
        return BoundField(self, form, name, initial)

    # ── Value conversion ──────────────────────────────────────────────────────

    def to_python(self, value: Any) -> Any:
        """Convert a raw widget value to the Python representation.

        Must be lenient during mid-keystroke calls: return ``None`` for
        values that cannot yet be converted rather than raising.
        """
        if value is None or value == "":
            return None
        return value

    def to_widget(self, value: Any) -> Any:
        """Convert a Python value to the widget representation (typically str)."""
        if value is None:
            return ""
        return str(value)

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self, value: Any) -> None:
        """Run all field-level validators against *value*.

        Raises ``ValidationError`` on the first failure.
        """
        for v in self.validators:
            if isinstance(v, Validator):
                v.validate(value)
            else:
                v(value)

    def clean(self, raw_value: Any) -> Any:
        """Full cleaning pipeline: convert → check required → validate.

        Returns the cleaned Python value, or raises ``ValidationError``.
        Called by ``BoundField.validate()`` on blur and by
        ``BaseForm.validate()`` on submission.
        """
        value = self.to_python(raw_value)
        if self.required and (value is None or value == ""):
            raise ValidationError("This field is required.")
        if value is not None:
            self.validate(value)
        return value

    def __repr__(self) -> str:
        return f"{type(self).__name__}(label={self.label!r})"


# ── Concrete field types ──────────────────────────────────────────────────────

class StringField(Field):
    """Single-line text field. Default widget: ``FormInput``."""

    def _default_widget_class(self) -> type:
        from .widgets import FormInput
        return FormInput


class IntegerField(Field):
    """Integer numeric input. Default widget: ``FormInput(type='integer')``."""

    def __init__(
        self,
        label: str,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        **kwargs: Any,
    ) -> None:
        validators = list(kwargs.pop("validators", ()))
        if min_value is not None:
            validators.append(MinValueValidator(min_value))
        if max_value is not None:
            validators.append(MaxValueValidator(max_value))
        self.min_value = min_value
        self.max_value = max_value
        # Force type="integer" on the widget (blocks non-numeric keystrokes).
        kwargs.setdefault("type", "integer")
        super().__init__(label, validators=validators, **kwargs)

    def _default_widget_class(self) -> type:
        from .widgets import FormInput
        return FormInput

    def to_python(self, value: Any) -> int | None:
        """Lenient conversion: returns ``None`` for mid-entry fragments."""
        raw = str(value).strip() if value is not None else ""
        if raw in ("", "-", "+"):
            return None
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None

    def to_widget(self, value: Any) -> str:
        return "" if value is None else str(value)

    def clean(self, raw_value: Any) -> int | None:
        raw_str = str(raw_value).strip() if raw_value is not None else ""
        value = self.to_python(raw_value)
        # Non-empty but unconvertible → format error (not mid-typing leniency).
        if raw_str and raw_str not in ("-", "+") and value is None:
            raise ValidationError("Enter a valid integer.")
        if self.required and value is None:
            raise ValidationError("This field is required.")
        if value is not None:
            self.validate(value)
        return value


class BooleanField(Field):
    """Boolean toggle. Default widget: ``FormCheckbox``."""

    def _default_widget_class(self) -> type:
        from .widgets import FormCheckbox
        return FormCheckbox

    def to_python(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def to_widget(self, value: Any) -> bool:
        return self.to_python(value) if value is not None else False


class ChoiceField(Field):
    """Selection from a fixed list. Default widget: ``FormSelect``."""

    def __init__(
        self,
        label: str,
        *,
        choices: list[tuple[str, Any]],
        **kwargs: Any,
    ) -> None:
        super().__init__(label, **kwargs)
        self.choices = choices
        # Pass choices through to the widget.
        self.widget_kwargs["choices"] = choices

    def _default_widget_class(self) -> type:
        from .widgets import FormSelect
        return FormSelect

    def to_python(self, value: Any) -> Any:
        from textual.widgets import Select
        if value is None or value is Select.BLANK:
            return None
        return value

    def to_widget(self, value: Any) -> Any:
        from textual.widgets import Select
        return Select.BLANK if value is None else value

    def clean(self, raw_value: Any) -> Any:
        value = self.to_python(raw_value)
        if self.required and value is None:
            raise ValidationError("This field is required.")
        if value is not None:
            valid_values = {v for _, v in self.choices}
            if value not in valid_values:
                raise ValidationError("Select a valid choice.")
            self.validate(value)
        return value


class TextField(Field):
    """Multi-line text field. Default widget: ``FormTextArea``."""

    def _default_widget_class(self) -> type:
        from .widgets import FormTextArea
        return FormTextArea
