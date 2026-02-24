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


class EmbeddedForm:
    """Marker object returned by Form.embed().

    Carries the source form class and prefix for expansion by FormMetaclass.
    """

    def __init__(self, form_class: type, prefix: str, title: str = "") -> None:
        self.form_class = form_class
        self.prefix = prefix
        self.title = title


class FormMetaclass(type):
    """Metaclass that extracts Field definitions from the class body.

    Handles EmbeddedForm expansion with prefix-based name mangling.
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

        # Process namespace for Field and EmbeddedForm instances
        to_remove = []
        for key, value in namespace.items():
            if isinstance(value, Field):
                if key in field_definitions:
                    raise FormError(
                        f"Field name {key!r} conflicts with inherited field."
                    )
                field_definitions[key] = value
                to_remove.append(key)
            elif isinstance(value, EmbeddedForm):
                embedded = value
                source_defs = getattr(
                    embedded.form_class, "_field_definitions", {}
                )
                for field_name, field_obj in source_defs.items():
                    prefixed_name = f"{embedded.prefix}_{field_name}"
                    if prefixed_name in field_definitions:
                        raise FormError(
                            f"Embedded field {prefixed_name!r} conflicts "
                            f"with existing field."
                        )
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
    ) -> None:
        self._data = data or {}
        self._layout_class = layout_class or self.__class__.layout_class
        self._instance_label_style = (
            label_style if label_style is not None else self.__class__.label_style
        )

        # Bind all fields
        self._bound_fields: OrderedDict[str, BoundField] = OrderedDict()
        field_defs: OrderedDict[str, Field] = getattr(
            self.__class__, "_field_definitions", OrderedDict()
        )
        for name, field in field_defs.items():
            bf = field.bind(self, name, self._data)
            # Apply form-level styles where the field didn't explicitly set them
            if not field._label_style_explicit:
                bf._label_style = self._instance_label_style
            if not field._help_style_explicit:
                bf._help_style = self.__class__.help_style
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
        """Get a bound field by name. Kept for backward compatibility."""
        try:
            return getattr(self, name)
        except AttributeError:
            raise AttributeError(
                f"{self.__class__.__name__!r} has no field {name!r}"
            )

    # ── Validation and cleaning ─────────────────────────────────

    def validate(self) -> bool:
        """Validate all fields. Returns True only if all fields are valid."""
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

        Calls validate() to check each field. If all pass, calls
        clean_form() for cross-field checks. Returns True if the
        entire form is valid.
        """
        if not self.validate():
            return False
        return self.clean_form()

    def clean_form(self) -> bool:
        """Override this for cross-field validation.

        Called only after all individual fields validate successfully.
        Return True if valid, False otherwise. Override should populate
        appropriate field errors if returning False.
        """
        return True

    # ── Data access ─────────────────────────────────────────────

    def get_data(self) -> dict[str, Any]:
        return {name: bf.value for name, bf in self._bound_fields.items()}

    def set_data(self, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if name in self._bound_fields:
                self._bound_fields[name].value = value

    # ── Layout ──────────────────────────────────────────────────

    def build_layout(self, id: str | None = None) -> FormLayout:
        """Instantiate and return the FormLayout for this Form instance."""
        from .layouts import DefaultFormLayout

        layout_cls = self._layout_class or DefaultFormLayout
        return layout_cls(form=self, id=id)

    # ── Embedding ───────────────────────────────────────────────

    @classmethod
    def embed(cls, prefix: str, title: str = "") -> EmbeddedForm:
        """Return an EmbeddedForm marker for use inside another form class body."""
        return EmbeddedForm(form_class=cls, prefix=prefix, title=title)


class Form(BaseForm):
    """Public alias for BaseForm. Use this to define forms."""

    pass
