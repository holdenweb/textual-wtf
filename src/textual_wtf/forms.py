"""Form classes — declarative base for form definitions."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from textual.message import Message

from .exceptions import AmbiguousFieldError, FormError, ValidationError
from .fields import Field
from .types import HelpStyle, LabelStyle

if TYPE_CHECKING:
    from .bound import BoundField
    from .layouts import FormLayout


class FormMetaclass(type):
    """Metaclass that extracts Field definitions from the class body.

    Handles direct Form-subclass assignment, expanding the inner form's
    fields into the parent with the variable name as an underscore prefix::

        class OrderForm(Form):
            billing = AddressForm   # → billing_street, billing_city, …
            shipping = AddressForm  # → shipping_street, shipping_city, …
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> FormMetaclass:
        field_definitions: OrderedDict[str, Field] = OrderedDict()

        # Inherit fields from bases
        for base in bases:
            if hasattr(base, "_field_definitions"):
                field_definitions.update(base._field_definitions)

        # Process namespace for Field instances and embedded Form subclasses
        to_remove = []
        for key, value in namespace.items():
            if isinstance(value, Field):
                if key in field_definitions:
                    raise FormError(
                        f"Field name {key!r} conflicts with inherited field."
                    )
                field_definitions[key] = value
                to_remove.append(key)
            elif (
                isinstance(value, type)
                and hasattr(value, "_field_definitions")
                and value._field_definitions  # skip BaseForm itself
            ):
                # Direct Form *class* assignment — auto-embed using
                # the class variable name as the prefix.
                source_defs = value._field_definitions
                for field_name, field_obj in source_defs.items():
                    prefixed_name = f"{key}_{field_name}"
                    if prefixed_name in field_definitions:
                        raise FormError(
                            f"Embedded field {prefixed_name!r} conflicts "
                            f"with existing field."
                        )
                    field_definitions[prefixed_name] = field_obj
                to_remove.append(key)
            elif (
                not isinstance(value, type)
                and hasattr(type(value), "_field_definitions")
                and type(value)._field_definitions  # skip bare BaseForm instances
            ):
                # Form *instance* assignment — embed with the variable name as
                # the prefix, applying any instance-level required= override.
                source_defs = type(value)._field_definitions
                required_override = getattr(value, "_instance_required", None)
                for field_name, field_obj in source_defs.items():
                    prefixed_name = f"{key}_{field_name}"
                    if prefixed_name in field_definitions:
                        raise FormError(
                            f"Embedded field {prefixed_name!r} conflicts "
                            f"with existing field."
                        )
                    if required_override is not None:
                        field_obj = field_obj._with_required(required_override)
                    field_definitions[prefixed_name] = field_obj
                to_remove.append(key)

        for key in to_remove:
            del namespace[key]

        namespace["_field_definitions"] = field_definitions
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls


class BaseForm(metaclass=FormMetaclass):
    """Base class for form definitions.

    Handles field binding, attribute access, validation, and data management.
    """

    layout_class: type[FormLayout] | None = None
    label_style: LabelStyle = "above"
    help_style: HelpStyle = "below"
    title: str = ""

    # ── Messages ────────────────────────────────────────────────

    @dataclass
    class Submitted(Message):
        """Posted when the user submits the form."""

        layout: FormLayout
        form: BaseForm

    @dataclass
    class Cancelled(Message):
        """Posted when the user cancels the form."""

        layout: FormLayout
        form: BaseForm

    # ── Constructor ─────────────────────────────────────────────

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        *,
        layout_class: type[FormLayout] | None = None,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        required: bool | None = None,
    ) -> None:
        self._data = data or {}
        self._layout_class = layout_class or self.__class__.layout_class
        self._instance_label_style = (
            label_style if label_style is not None else self.__class__.label_style
        )
        self._instance_help_style = (
            help_style if help_style is not None else self.__class__.help_style
        )
        # Stored so the metaclass can read it when this instance is used as
        # a class-level embedded-form assignment (e.g. shipping = AddressForm(required=False)).
        self._instance_required: bool | None = required
        # Flag set by add_error() during clean_form(); reset at each clean() call
        self._clean_form_errored: bool = False

        # Bind all fields
        self._bound_fields: OrderedDict[str, BoundField] = OrderedDict()
        field_defs: OrderedDict[str, Field] = getattr(
            self.__class__, "_field_definitions", OrderedDict()
        )
        for name, field in field_defs.items():
            # Apply form-instance-level required override for direct (non-embedded) use.
            # For embedded instances the metaclass already baked the override into
            # the cloned field definitions, so this is a no-op in that path.
            if required is not None:
                field = field._with_required(required)
            bf = field.bind(self, name, self._data)
            # Apply form-level styles where the field didn't explicitly set them
            if not field._label_style_explicit:
                bf._label_style = self._instance_label_style
            if not field._help_style_explicit:
                bf._help_style = self._instance_help_style
            self._bound_fields[name] = bf

    # ── Field access ────────────────────────────────────────────

    @property
    def bound_fields(self) -> OrderedDict[str, BoundField]:
        return self._bound_fields

    @property
    def fields(self) -> OrderedDict[str, BoundField]:
        return self._bound_fields

    def __getattr__(self, name: str) -> BoundField:
        # Guard against recursion during __init__
        if name.startswith("_"):
            raise AttributeError(name)

        bf = self._bound_fields.get(name)
        if bf is not None:
            return bf

        # Unqualified name resolution for embedded forms
        candidates = []
        suffix = f"_{name}"
        for field_name in self._bound_fields:
            if field_name.endswith(suffix):
                candidates.append(field_name)

        if len(candidates) == 1:
            return self._bound_fields[candidates[0]]
        elif len(candidates) > 1:
            raise AmbiguousFieldError(name, candidates)

        raise AttributeError(
            f"{self.__class__.__name__!r} has no field {name!r}"
        )

    def get_field(self, name: str) -> BoundField:
        """Get a bound field by name."""
        try:
            return getattr(self, name)
        except AttributeError:
            raise AttributeError(
                f"{self.__class__.__name__!r} has no field {name!r}"
            )

    # ── Validation and cleaning ─────────────────────────────────

    def validate(self) -> bool:
        """Validate all fields.  Returns True only if all fields are valid."""
        all_valid = True
        for bf in self._bound_fields.values():
            if not bf.validate():
                all_valid = False
        return all_valid

    def is_valid(self) -> bool:
        """Alias for validate()."""
        return self.validate()

    def clean(self) -> bool:
        """Full form-level cleaning pipeline.

        Calls ``validate()`` to check each field.  If all pass, calls
        ``clean_form()`` for cross-field checks.  Any calls to
        ``add_error()`` inside ``clean_form()`` also cause ``clean()`` to
        return ``False``, even if ``clean_form()`` returns ``True``.

        After ``clean_form()`` completes, all field widgets are notified so
        that any errors set via the backward-compatible direct-assignment
        style are reflected in the UI.
        """
        if not self.validate():
            return False
        self._clean_form_errored = False
        result = self.clean_form()
        # Notify all FieldWidgets so that errors set inside clean_form()
        # (via add_error or direct assignment) propagate to the UI.
        self._sync_field_error_listeners()
        return result and not self._clean_form_errored

    def clean_form(self) -> bool:
        """Override for cross-field validation.

        Called only after all individual fields pass ``validate()``.
        Return ``True`` if valid, ``False`` otherwise.

        Use ``self.add_error(field_name, message)`` to attach errors to
        specific fields — this is preferred over direct attribute assignment.
        """
        return True

    def add_error(self, field_name: str, message: str) -> None:
        """Attach a cross-field error to a named field.

        Intended for use inside ``clean_form()``.  The error is visible in
        the field's error label when the UI is next refreshed (which happens
        automatically at the end of ``clean()``).

        Raises ``FormError`` if ``field_name`` does not exist.
        """
        bf = self._bound_fields.get(field_name)
        if bf is None:
            raise FormError(
                f"{self.__class__.__name__!r} has no field {field_name!r}."
            )
        bf.controller.errors.append(message)
        bf.controller.has_error = True
        bf.controller.error_messages = list(bf.controller.errors)
        self._clean_form_errored = True

    def _sync_field_error_listeners(self) -> None:
        """Push current error state from every controller to its listeners."""
        for bf in self._bound_fields.values():
            bf.controller._notify_errors()

    # ── Data access ─────────────────────────────────────────────

    def get_data(self) -> dict[str, Any]:
        return {name: bf.value for name, bf in self._bound_fields.items()}

    def set_data(self, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if name in self._bound_fields:
                bf = self._bound_fields[name]
                try:
                    bf.value = bf._field.to_python(value)
                except ValidationError:
                    bf.value = value

    # ── Layout ──────────────────────────────────────────────────

    def build_layout(self, id: str | None = None) -> FormLayout:
        """Instantiate and return the FormLayout for this Form instance."""
        from .layouts import DefaultFormLayout

        layout_cls = self._layout_class or DefaultFormLayout
        return layout_cls(form=self, id=id)


class Form(BaseForm):
    """Public alias for BaseForm. Use this to define forms."""

    pass
