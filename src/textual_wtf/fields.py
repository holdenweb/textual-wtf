"""Field classes — immutable declarative configuration for form fields."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from .exceptions import FieldError, ValidationError
from .types import HelpStyle, LabelStyle
from .validators import MaxValue, MinValue, Validator
from .widgets import FormCheckbox, FormInput, FormSelect, FormTextArea

if TYPE_CHECKING:
    from .bound import BoundField
    from .forms import BaseForm


class Field:
    """Immutable declarative configuration for a single form field.

    Defined at class level on a Form subclass and shared across all
    instances of that form. Never holds runtime state.
    """

    default_widget_class: type | None = None

    def __init__(
        self,
        label: str,
        *,
        initial: Any = None,
        required: bool = False,
        disabled: bool = False,
        validators: list[Validator | Callable[..., Any]] | tuple[()] = (),
        help_text: str = "",
        label_style: LabelStyle = "above",
        help_style: HelpStyle = "below",
        widget_class: type | None = None,
        **widget_kwargs: Any,
    ) -> None:
        self.label = label
        self.initial = initial
        self.required = required
        self.disabled = disabled
        self.validators = list(validators)
        self.help_text = help_text
        self.label_style: LabelStyle = label_style
        self.help_style: HelpStyle = help_style
        self._label_style_explicit = label_style != "above"
        self._help_style_explicit = help_style != "below"
        self.widget_class = widget_class or self.default_widget_class
        self.widget_kwargs = widget_kwargs

    def bind(
        self,
        form: BaseForm,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> BoundField:
        """Create a BoundField for this Field within a specific form instance."""
        from .bound import BoundField

        return BoundField(field=self, form=form, name=name, data=data or {})

    def to_python(self, value: Any) -> Any:
        """Convert a raw widget value to the appropriate Python type.

        Base implementation is a passthrough. Subclasses override
        where type coercion is needed (e.g. IntegerField).
        """
        return value


class StringField(Field):
    """Single-line text field. Default widget: FormInput."""

    default_widget_class = FormInput


class IntegerField(Field):
    """Integer numeric input. Default widget: FormInput with restricted input."""

    default_widget_class = FormInput

    def __init__(
        self,
        label: str,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(label, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        if min_value is not None:
            self.validators.append(MinValue(min_value))
        if max_value is not None:
            self.validators.append(MaxValue(max_value))
        self.widget_kwargs.setdefault("restrict", r"[0-9\-]*")

    def to_python(self, value: Any) -> Any:
        """Coerce to int. Returns None for empty/None values."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Enter a whole number (got {value!r}).")


class BooleanField(Field):
    """Boolean toggle. Default widget: FormCheckbox."""

    default_widget_class = FormCheckbox

    def __init__(self, label: str, **kwargs: Any) -> None:
        kwargs.setdefault("initial", False)
        super().__init__(label, **kwargs)


class ChoiceField(Field):
    """Selection from a fixed list. Default widget: FormSelect."""

    default_widget_class = FormSelect

    def __init__(
        self,
        label: str,
        *,
        choices: list[tuple[str, Any]],
        **kwargs: Any,
    ) -> None:
        if not choices:
            raise FieldError("ChoiceField requires a non-empty choices list.")
        super().__init__(label, **kwargs)
        self.choices = choices


class TextField(Field):
    """Multi-line text field. Default widget: FormTextArea."""

    default_widget_class = FormTextArea
