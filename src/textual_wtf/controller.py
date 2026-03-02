"""FieldController — non-widget holder of a field's runtime state and validation logic."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from .exceptions import FormError, ValidationError

if TYPE_CHECKING:
    from .fields import Field
    from .forms import BaseForm


class FieldController:
    """Holds the runtime value, error state, and validation logic for one field.

    A plain Python class — no Textual inheritance.  Created by
    ``BoundField.__init__``; referenced by the BoundField and (when mounted)
    by a ``FieldWidget``.

    Listeners
    ---------
    ``_value_listeners``
        Called when ``value`` is set *externally* (programmatic assignment,
        ``set_data``, etc.).  Signature: ``(new_value: Any) -> None``.
        **Not** fired during widget-event handling to avoid circular updates.

    ``_error_listeners``
        Called whenever the error state changes.
        Signature: ``(has_error: bool, error_messages: list[str]) -> None``.
        Fired by ``_set_errors``, ``_clear_errors``, and ``add_error``.
    """

    def __init__(
        self,
        field: Field,
        form: BaseForm,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self._field = field
        self._form = form
        self._name = name

        # ── Mutable state ──────────────────────────────────────
        self.errors: list[str] = []
        self.has_error: bool = False
        self.error_messages: list[str] = []
        self.is_dirty: bool = False

        # ── Render guard ───────────────────────────────────────
        # Set to True by claim() the first time a widget is produced from
        # this controller; prevents the same field being mounted twice.
        self._consumed: bool = False

        # ── Listener registries ────────────────────────────────
        self._value_listeners: list[Callable[[Any], None]] = []
        self._error_listeners: list[Callable[[bool, list[str]], None]] = []

        # ── Initial value ──────────────────────────────────────
        data = data or {}
        raw = data[name] if name in data else field.initial
        try:
            self._value: Any = field.to_python(raw)
        except ValidationError:
            self._value = raw

    # ── Value property ─────────────────────────────────────────

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the value externally; notifies value listeners."""
        self._value = new_value
        self._notify_value()

    # ── Render guard ───────────────────────────────────────────

    def claim(self) -> None:
        """Mark this controller as consumed by a widget.

        Raises :class:`~textual_wtf.FormError` if a widget has already been
        produced from this controller (i.e. the same field has been rendered
        twice in the same layout).  Must be called at the start of
        ``BoundField.__call__`` and ``BoundField.simple_layout``.
        """
        if self._consumed:
            raise FormError(
                f"Field {self._name!r} has already been rendered in this layout."
            )
        self._consumed = True

    def apply_required(self, required: bool) -> None:
        """Override the required state at render time (highest priority in the cascade).

        Clones the underlying :class:`~textual_wtf.fields.Field`, adjusts its
        ``required`` flag and validator list, and updates the controller's own
        ``_field`` reference so that subsequent validation uses the new state.
        """
        import copy
        from .validators import Required

        clone = copy.copy(self._field)
        clone.required = required
        clone.validators = [v for v in self._field.validators if not isinstance(v, Required)]
        if required:
            clone.validators.insert(0, Required())
        clone._required_explicitly_set = True
        self._field = clone

    # ── Listener registration ──────────────────────────────────

    def add_value_listener(self, callback: Callable[[Any], None]) -> None:
        """Register a callback invoked on external value changes."""
        self._value_listeners.append(callback)

    def add_error_listener(
        self, callback: Callable[[bool, list[str]], None]
    ) -> None:
        """Register a callback invoked on any error-state change."""
        self._error_listeners.append(callback)

    def remove_error_listener(
        self, callback: Callable[[bool, list[str]], None]
    ) -> None:
        """Deregister a previously registered error-state callback."""
        try:
            self._error_listeners.remove(callback)
        except ValueError:
            pass

    # ── Validation ─────────────────────────────────────────────

    def validate(self) -> bool:
        """Full submit-path validation.  Updates error state and notifies listeners."""
        result = self._validate_for("submit")
        self._notify_errors()
        return result

    def validate_for(self, event: str) -> bool:
        """Public alias for ``_validate_for``.  Notifies error listeners."""
        result = self._validate_for(event)
        self._notify_errors()
        return result

    def _validate_for(self, event: str) -> bool:
        """Core validation pipeline.  Updates state; does NOT notify listeners.

        Callers that need UI sync should call ``_notify_errors()`` (or use
        the public ``validate`` / ``validate_for`` methods which do so
        automatically).
        """
        failures: list[str] = []

        # 1. Type coercion
        try:
            python_value = self._field.to_python(self._value)
        except ValidationError as e:
            failures.append(e.message)
            self._set_errors(failures)
            return False

        self._value = python_value

        # 2. Skip further validation for empty optional fields.
        #    Required validator (added to validators list when required=True)
        #    handles the required-and-empty case; other validators are written
        #    to skip None, so we only need to skip empty strings here.
        is_empty = python_value is None or (
            isinstance(python_value, str) and python_value.strip() == ""
        )
        if is_empty and not self._field.required:
            self._clear_errors()
            return True

        # 3. Run validators whose validate_on includes this event.
        for v in self._field.validators:
            if event in v.validate_on:
                result = v.validate(python_value)
                if not result.is_valid:
                    for desc in result.failure_descriptions:
                        failures.append(desc)

        if failures:
            self._set_errors(failures)
            return False

        self._clear_errors()
        return True

    # ── Cross-field error injection ────────────────────────────

    def add_error(self, message: str) -> None:
        """Append a cross-field error message and notify listeners immediately."""
        self.errors.append(message)
        self.has_error = True
        self.error_messages = list(self.errors)
        self._notify_errors()

    # ── Widget-event integration (called by FieldWidget / ControllerAwareLayout)

    def handle_widget_input(self, raw_value: Any, event: str = "change") -> bool:
        """Process a value change originating from the inner widget.

        Updates ``_value``, runs event validators, and notifies error listeners.
        Does **not** fire value listeners (to avoid syncing the value back into
        the widget that just provided it).  Returns whether the field is
        currently valid for this event.
        """
        try:
            self._value = self._field.to_python(raw_value)
        except ValidationError:
            self._value = raw_value
        self.is_dirty = True
        result = self._validate_for(event)
        self._notify_errors()
        return result

    # ── Notification helpers ───────────────────────────────────

    def _notify_value(self) -> None:
        for cb in self._value_listeners:
            cb(self._value)

    def _notify_errors(self) -> None:
        for cb in self._error_listeners:
            cb(self.has_error, list(self.error_messages))

    def _set_errors(self, failures: list[str]) -> None:
        self.errors = failures
        self.has_error = True
        self.error_messages = list(failures)

    def _clear_errors(self) -> None:
        self.errors = []
        self.has_error = False
        self.error_messages = []
