"""BoundField — mutable runtime state for one field within one form instance.

BoundField is a plain Python object.  It holds the field's current value,
error state, and dirty flag, and keeps a reference to the inner Textual
widget once the field has been rendered.

Lifecycle
---------
1.  ``Field.bind()`` creates a BoundField during ``BaseForm.__init__()``.
    No Textual context exists yet; the object is safe to use immediately.

2.  ``BoundField.__call__(**kwargs)`` is called inside
    ``FormLayout.compose_form()``.  It instantiates the inner widget,
    wraps it in a ``FieldContainer``, stores references to both, and
    returns the ``FieldContainer`` for Textual to mount.

3.  Once mounted, ``FieldContainer`` handles DOM events and calls back
    into BoundField to keep ``_value`` in sync.

Value synchronisation
---------------------
*  User types → FormInput fires ``FormValueChanged`` → FieldContainer
   handler sets ``bf._value`` directly (bypassing the setter to avoid
   a feedback loop) and marks ``is_dirty``.

*  Programmatic ``form.name.value = x`` → setter stores ``_value`` and,
   if the inner widget exists, pushes the widget representation via
   ``_inner.value = field.to_widget(x)``.  The ``_syncing`` flag silences
   the echo that would otherwise arrive via ``FormValueChanged``.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .exceptions import FormError, ValidationError
from .fields import _UNSET

if TYPE_CHECKING:
    from .fields import Field
    from .forms import BaseForm
    from .layouts import FieldContainer


class BoundField:
    """Plain-Python runtime state for a single field in a form instance."""

    # ── Construction ─────────────────────────────────────────────────────────

    def __init__(
        self,
        field: Field,
        form: BaseForm,
        name: str,
        initial: Any = None,
    ) -> None:
        self.field = field
        self.form = form
        self.name = name

        self._initial_value: Any = initial if initial is not None else field.initial
        self.errors: list[str] = []
        self.is_dirty: bool = False
        self._disabled: bool = field.disabled

        # Set by __call__ at render time.
        self._inner: Any = None
        self._container: FieldContainer | None = None
        self._rendered: bool = False

        # Render-time overrides set by __call__.
        self._render_label_style: str | None = None
        self._render_help_style: str | None = None
        self._render_disabled: bool | None = None
        self._render_extra_validators: list | None = None
        self._render_widget_kwargs: dict[str, Any] = {}

        # Canonical value store.
        self._value: Any = self._initial_value

        # Sync guard: True while pushing a value to the inner widget so the
        # echo from FormValueChanged can be ignored by FieldContainer.
        self._syncing: bool = False

    # ── Field attribute delegation (read-only) ────────────────────────────────

    @property
    def label(self) -> str:
        return self.field.label

    @property
    def initial(self) -> Any:
        return self.field.initial

    @property
    def required(self) -> bool:
        return self.field.required

    @property
    def help_text(self) -> str:
        return self.field.help_text

    @property
    def validators(self) -> list:
        return self.field.validators

    # ── disabled ──────────────────────────────────────────────────────────────

    @property
    def disabled(self) -> bool:
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._disabled = value
        if self._inner is not None:
            self._inner.disabled = value

    # ── value ─────────────────────────────────────────────────────────────────

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        self._value = val
        if val != self._initial_value:
            self.is_dirty = True
        # Push to widget if mounted; _syncing tells FieldContainer to ignore
        # the resulting FormValueChanged echo.
        if self._inner is not None:
            self._syncing = True
            try:
                self._inner.value = self.field.to_widget(val)
            except Exception:
                pass
            finally:
                self._syncing = False

    # ── Style resolution (call-site > field > form > built-in default) ────────

    def _effective_label_style(self) -> str:
        if self._render_label_style is not None:
            return self._render_label_style
        if self.field._label_style is not _UNSET:
            return self.field._label_style  # type: ignore[return-value]
        return getattr(self.form, "label_style", "above")

    def _effective_help_style(self) -> str:
        if self._render_help_style is not None:
            return self._render_help_style
        if self.field._help_style is not _UNSET:
            return self.field._help_style  # type: ignore[return-value]
        return getattr(self.form, "help_style", "below")

    # ── Callable interface ────────────────────────────────────────────────────

    def __call__(
        self,
        *,
        label_style: str | None = None,
        help_style: str | None = None,
        disabled: bool | None = None,
        validators: list | None = None,
        **widget_kwargs: Any,
    ) -> FieldContainer:
        """Configure for rendering and return a ``FieldContainer`` widget.

        Called inside ``FormLayout.compose_form()``; the returned
        ``FieldContainer`` is what Textual mounts.  Raises ``FormError``
        if this field has already been rendered in the current layout.
        """
        if self._rendered:
            raise FormError(
                f"Field '{self.name}' has already been rendered in this layout."
                " Each field may only be yielded once."
            )
        self._rendered = True

        # Store render-time overrides for later querying.
        self._render_label_style = label_style
        self._render_help_style = help_style
        if disabled is not None:
            self._render_disabled = disabled
        if validators is not None:
            self._render_extra_validators = validators
        self._render_widget_kwargs = widget_kwargs

        # Resolve effective disabled state.
        is_disabled = (
            self._render_disabled
            if self._render_disabled is not None
            else self._disabled
        )

        # Merge widget kwargs: field defaults < call-site overrides.
        merged: dict[str, Any] = {**self.field.widget_kwargs, **widget_kwargs}
        if is_disabled:
            merged["disabled"] = True
        if self._effective_label_style() == "placeholder":
            merged["placeholder"] = self.field.label

        # Instantiate the inner widget.
        self._inner = self.field.widget_class(bound_field=self, **merged)

        # Sync initial value into the inner widget immediately.
        if self._initial_value is not None:
            try:
                self._inner.value = self.field.to_widget(self._initial_value)
            except Exception:
                pass

        # Create the FieldContainer that wraps label + widget + help + error.
        from .layouts import FieldContainer
        self._container = FieldContainer(
            self,
            self._inner,
            self._effective_label_style(),
            self._effective_help_style(),
        )
        return self._container

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> bool:
        """Run ``field.clean(self._value)``.

        Populates ``errors`` and notifies the ``FieldContainer`` to update
        the error display.  Returns ``True`` if valid.
        """
        extra = self._render_extra_validators or []
        saved = self.field.validators
        if extra:
            self.field.validators = saved + extra
        try:
            self.field.clean(self._value)
        except ValidationError as exc:
            self.errors = [exc.message]
            return False
        else:
            self.errors = []
            return True
        finally:
            if extra:
                self.field.validators = saved
            # Always update error display regardless of outcome.
            if self._container is not None:
                self._container.update_errors()

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def has_error(self) -> bool:
        return bool(self.errors)

    @property
    def error_message(self) -> str:
        return self.errors[0] if self.errors else ""

    def __repr__(self) -> str:
        return (
            f"BoundField(name={self.name!r}, "
            f"field={self.field!r}, "
            f"value={self._value!r})"
        )
