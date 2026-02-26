"""Field classes — immutable declarative configuration for form fields."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from .exceptions import FieldError, ValidationError
from .types import HelpStyle, LabelStyle
from .validators import (
    FunctionValidator,
    MaxLength,
    MaxValue,
    MinLength,
    MinValue,
    Required,
    Validator,
)
from .widgets import FormCheckbox, FormInput, FormSelect, FormTextArea

if TYPE_CHECKING:
    from .bound import BoundField
    from .forms import BaseForm


# Sentinel used to distinguish an explicit ``required=False`` from an
# omitted ``required`` argument.  Only _UNSET means "apply cascade".
_UNSET: object = object()


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
        required: bool | object = _UNSET,
        disabled: bool = False,
        validators: list[Validator | Callable[..., Any]] | tuple[()] = (),
        help_text: str = "",
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        widget_class: type | None = None,
        **widget_kwargs: Any,
    ) -> None:
        self.label = label
        self.initial = initial
        # Track whether required was passed explicitly so Form-instance-level
        # required= overrides know whether to apply.
        self._required_explicitly_set: bool = required is not _UNSET
        self.required: bool = False if required is _UNSET else bool(required)
        self.disabled = disabled
        self.validators = [
            v if isinstance(v, Validator) else FunctionValidator(v)
            for v in validators
        ]
        # required=True is implemented as the first validator so the pipeline
        # is fully unified — no special-case code in FieldController.
        if self.required:
            self.validators.insert(0, Required())
        self.help_text = help_text
        self._label_style_explicit = label_style is not None
        self._help_style_explicit = help_style is not None
        self.label_style: LabelStyle = label_style if label_style is not None else "above"
        self.help_style: HelpStyle = help_style if help_style is not None else "below"
        self.widget_class = widget_class or self.default_widget_class
        self.widget_kwargs = widget_kwargs

    def _with_required(self, required: bool) -> Field:
        """Return a shallow clone with the required flag overridden.

        If this field had ``required`` set *explicitly* (the caller passed
        ``required=True`` or ``required=False``), the field's own setting wins
        and ``self`` is returned unchanged.  Otherwise a clone is returned with
        the Required validator added or removed as appropriate.
        """
        if self._required_explicitly_set:
            return self  # field-level explicit setting always wins
        import copy
        clone = copy.copy(self)
        clone.required = required
        # Rebuild validators: strip any existing Required, re-add if needed.
        clone.validators = [
            v for v in self.validators if not isinstance(v, Required)
        ]
        if required:
            clone.validators.insert(0, Required())
        # Mark clone as explicitly set so further cascades don't change it.
        clone._required_explicitly_set = True
        return clone

    def bind(
        self,
        form: BaseForm,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> BoundField:
        """Create a BoundField for this Field within a specific form instance."""
        from .bound import BoundField

        return BoundField(field=self, form=form, name=name, data=data or {})

    def _add_length_validators(
        self,
        min_length: int | None,
        max_length: int | None,
    ) -> None:
        """Append MinLength / MaxLength validators.

        Convenience for subclasses that support ``min_length`` /
        ``max_length`` keyword arguments; call from ``__init__`` after
        ``super().__init__()``.
        """
        if min_length is not None:
            self.validators.append(MinLength(min_length))
        if max_length is not None:
            self.validators.append(MaxLength(max_length))

    def to_python(self, value: Any) -> Any:
        """Convert a raw widget value to the appropriate Python type.

        Base implementation is a passthrough. Subclasses override
        where type coercion is needed (e.g. IntegerField).
        """
        return value


class StringField(Field):
    """Single-line text field. Default widget: FormInput."""

    default_widget_class = FormInput

    def __init__(
        self,
        label: str,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(label, **kwargs)
        self._add_length_validators(min_length, max_length)


class IntegerField(Field):
    """Integer numeric input. Default widget: FormInput with restricted input."""

    default_widget_class = FormInput

    def __init__(
        self,
        label: str,
        *,
        minimum: int | None = None,
        maximum: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(label, **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        if minimum is not None:
            self.validators.append(MinValue(minimum))
        if maximum is not None:
            self.validators.append(MaxValue(maximum))
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

    def __init__(
        self,
        label: str,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(label, **kwargs)
        self._add_length_validators(min_length, max_length)
