"""Form metaclass, BaseForm, and Form for textual-wtf."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .bound_fields import BoundField
from .exceptions import AmbiguousFieldError, FormError
from .fields import Field

if TYPE_CHECKING:
    from .layouts import FormLayout


# ── ComposedForm marker ───────────────────────────────────────────────────────

class ComposedForm:
    """Marker object returned by ``Form.compose()``.

    ``FormMetaclass`` expands this in place, prefixing all field names.
    """

    def __init__(self, form_class: type, prefix: str, title: str = "") -> None:
        self.form_class = form_class
        self.prefix = prefix
        self.title = title


# ── Metaclass ─────────────────────────────────────────────────────────────────

class FormMetaclass(type):
    """Collects ``Field`` declarations and expands ``ComposedForm`` markers."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        base_fields: dict[str, Field] = {}

        # Inherit fields from base Form classes (in MRO order, earlier wins).
        for base in reversed(bases):
            if hasattr(base, "_base_fields"):
                base_fields.update(base._base_fields)

        # Process this class's namespace in declaration order.
        for key, val in namespace.items():
            if isinstance(val, Field):
                base_fields[key] = val
            elif isinstance(val, ComposedForm):
                if not hasattr(val.form_class, "_base_fields"):
                    raise FormError(
                        f"'{val.form_class}' is not a Form class."
                    )
                for fname, field in val.form_class._base_fields.items():
                    prefixed = f"{val.prefix}_{fname}"
                    if prefixed in base_fields:
                        raise FormError(
                            f"Field name collision after composition: '{prefixed}'."
                        )
                    base_fields[prefixed] = field

        # Build clean namespace (strip Field / ComposedForm entries, add _base_fields).
        new_namespace: dict[str, Any] = {
            k: v
            for k, v in namespace.items()
            if not isinstance(v, (Field, ComposedForm))
        }
        new_namespace["_base_fields"] = base_fields

        return super().__new__(mcs, name, bases, new_namespace)


# ── BaseForm ──────────────────────────────────────────────────────────────────

class BaseForm:
    """Base implementation; not normally used directly — use ``Form``."""

    #: Default layout class used by ``render()``.  Set to a ``FormLayout``
    #: subclass on the ``Form`` subclass to customise.
    layout_class: type | None = None

    #: Form-wide default label style.  Overridden per-field or per-render-call.
    label_style: str = "above"

    #: Form-wide default help style.
    help_style: str = "below"

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        *,
        layout_class: type | None = None,
    ) -> None:
        self._layout_class = layout_class or type(self).layout_class

        # Create one BoundField per declared field.
        self.bound_fields: dict[str, BoundField] = {}
        for name, field in self._base_fields.items():  # type: ignore[attr-defined]
            initial = data.get(name) if data else None
            bf = field.bind(self, name, initial)
            self.bound_fields[name] = bf
            # Expose as instance attribute so form.fieldname works.
            object.__setattr__(self, name, bf)

    # ── Field access ──────────────────────────────────────────────────────────

    @property
    def fields(self) -> dict[str, BoundField]:
        """Alias for ``bound_fields``."""
        return self.bound_fields

    def __getattr__(self, name: str) -> BoundField:
        """Return the ``BoundField`` for *name*, with SQL-style resolution.

        * Exact match first.
        * If not found, search for fields whose name *ends with* ``_<name>``
          (unqualified suffix lookup for composed forms).
        * Raises ``AmbiguousFieldError`` if more than one suffix match.
        * Raises ``AttributeError`` if not found at all.
        """
        # Avoid recursion before bound_fields is set during __init__.
        if name.startswith("_") or name == "bound_fields":
            raise AttributeError(name)

        bf_dict = object.__getattribute__(self, "bound_fields")

        # 1. Exact match.
        if name in bf_dict:
            return bf_dict[name]

        # 2. Suffix match for composed-form unqualified access.
        suffix = f"_{name}"
        candidates = [k for k in bf_dict if k.endswith(suffix)]
        if len(candidates) == 1:
            return bf_dict[candidates[0]]
        if len(candidates) > 1:
            raise AmbiguousFieldError(name, candidates)

        raise AttributeError(
            f"'{type(self).__name__}' has no field '{name}'."
        )

    def get_field(self, name: str) -> BoundField:
        """Explicit field accessor (kept for backward compatibility)."""
        return getattr(self, name)

    # ── Data access ───────────────────────────────────────────────────────────

    def get_data(self) -> dict[str, Any]:
        """Return ``{name: value}`` for all fields."""
        return {name: bf.value for name, bf in self.bound_fields.items()}

    def set_data(self, data: dict[str, Any]) -> None:
        """Set field values from *data*; unknown keys are ignored."""
        for name, value in data.items():
            if name in self.bound_fields:
                self.bound_fields[name].value = value

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> bool:
        """Validate all fields.  Returns ``True`` only if all are valid."""
        return all(bf.validate() for bf in self.bound_fields.values())

    def is_valid(self) -> bool:
        """Alias for ``validate()``."""
        return self.validate()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, id: str | None = None) -> FormLayout:
        """Instantiate and return the layout widget, ready to mount."""
        from .layouts import DefaultFormLayout

        layout_cls = self._layout_class or DefaultFormLayout
        return layout_cls(self, id=id)

    def __repr__(self) -> str:
        fields = list(self.bound_fields)
        return f"{type(self).__name__}(fields={fields})"


# ── Public Form class ─────────────────────────────────────────────────────────

class Form(BaseForm, metaclass=FormMetaclass):
    """Declarative base class for form definitions.

    Define fields as class-level ``Field`` instances::

        class ContactForm(Form):
            label_style = "beside"         # form-wide default

            name  = StringField(label="Name",  required=True)
            email = StringField(label="Email", validators=[EmailValidator()])
            notes = TextField(label="Notes",   help_style="tooltip")

    Instantiate to get a form with ``BoundField`` instances::

        form = ContactForm()
        form.name.value = "Alice"
        layout = form.render()             # yields a FormLayout widget
    """

    # ── Class method for composition ─────────────────────────────────────────

    @classmethod
    def compose(cls, prefix: str, title: str = "") -> ComposedForm:
        """Return a ``ComposedForm`` marker for embedding in another form.

        Usage::

            class OrderForm(Form):
                billing  = AddressForm.compose(prefix="billing")
                shipping = AddressForm.compose(prefix="shipping")
                notes    = TextField(label="Notes")
        """
        return ComposedForm(cls, prefix, title)
