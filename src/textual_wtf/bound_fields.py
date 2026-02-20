"""BoundField — mutable runtime state for one field within one form instance.

``BoundField`` is both a plain-Python data object (holding the field's current
value, error state, and dirty flag) *and* a Textual ``Vertical`` container
widget.  When mounted it composes its own label, inner input widget, optional
help text, and error display.

Synchronisation between the inner widget and ``BoundField.value`` is
achieved via Textual's reactive system:

* User types → inner widget fires ``FormValueChanged`` → ``on_form_value_changed``
  sets ``self.value`` (the reactive).
* Programmatic ``bound_field.value = x`` → ``watch_value`` fires → updates
  inner widget directly.

Because Textual does **not** post ``Input.Changed`` (etc.) when a widget's
value is set programmatically, no re-entrancy guard is needed for the common
path.  The ``_from_widget`` flag is used only to suppress the programmatic
sync-back when the reactive fired from user input (so we don't overwrite a
partially-typed string with its round-tripped value).
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static

from .exceptions import FormError, ValidationError
from .fields import _UNSET
from .widgets import FormBlurred, FormValueChanged

if TYPE_CHECKING:
    from .fields import Field
    from .forms import BaseForm


class BoundField(Vertical):
    """Runtime state for a field; also a Textual ``Vertical`` container."""

    DEFAULT_CSS = """
    BoundField {
        height: auto;
        margin-bottom: 1;
    }
    BoundField .field-label {
        color: $text;
    }
    BoundField .field-row {
        height: auto;
    }
    BoundField .field-help {
        color: $text-muted;
        text-style: italic;
    }
    BoundField .field-error {
        color: $error;
    }
    """

    # ── Reactives ────────────────────────────────────────────────────────────

    #: Current Python value.  Setting triggers ``watch_value``.
    value: reactive[Any] = reactive(None, init=False)
    #: ``True`` when ``errors`` is non-empty.
    has_error: reactive[bool] = reactive(False, init=False)
    #: First error message (empty string when valid).
    error_message: reactive[str] = reactive("", init=False)

    # ── Construction ─────────────────────────────────────────────────────────

    def __init__(
        self,
        field: Field,
        form: BaseForm,
        name: str,
        initial: Any = None,
    ) -> None:
        super().__init__()
        self.field = field
        self.form = form
        self.name = name

        # The effective initial value: constructor arg > field.initial.
        self._initial_value: Any = initial if initial is not None else field.initial

        # Mutable per-instance state.
        self.errors: list[str] = []
        self.is_dirty: bool = False
        self._disabled: bool = field.disabled

        # Internal flags / references.
        self._from_widget: bool = False  # suppress sync-back during user input
        self._rendered: bool = False     # duplicate-render guard
        self._inner: Any = None          # reference to the mounted inner widget

        # Render-time overrides — set by __call__ before compose() runs.
        self._render_label_style: str | None = None
        self._render_help_style: str | None = None
        self._render_disabled: bool | None = None
        self._render_extra_validators: list | None = None
        self._render_widget_kwargs: dict[str, Any] = {}

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

    # ── disabled — mutable, reflected to inner widget ─────────────────────────

    @property
    def disabled(self) -> bool:  # type: ignore[override]
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._disabled = value
        if self._inner is not None:
            self._inner.disabled = value

    # ── Effective style resolution (call-site > field > form > built-in) ──────

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
    ) -> "BoundField":
        """Configure for rendering and return *self*.

        Called inside ``FormLayout.compose_form()`` to yield the field into
        the widget tree.  Raises ``FormError`` if already rendered.

        Any supplied kwargs override the ``Field`` declaration for this render.
        ``widget_kwargs`` are merged with (and override) ``field.widget_kwargs``.
        """
        if self._rendered:
            raise FormError(
                f"Field '{self.name}' has already been rendered in this layout."
                " Each field may only be yielded once."
            )
        self._rendered = True
        if label_style is not None:
            self._render_label_style = label_style
        if help_style is not None:
            self._render_help_style = help_style
        if disabled is not None:
            self._render_disabled = disabled
        if validators is not None:
            self._render_extra_validators = validators
        self._render_widget_kwargs = widget_kwargs
        return self

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> bool:
        """Run ``field.clean(self.value)``.

        Populates ``errors``, ``has_error``, and ``error_message``.
        Returns ``True`` if valid.
        """
        # Build effective validator list (field + call-site extras).
        if self._render_extra_validators:
            import copy
            saved = self.field.validators
            self.field.validators = saved + self._render_extra_validators
        try:
            self.field.clean(self.value)
        except ValidationError as exc:
            self.errors = [exc.message]
            self.has_error = True
            self.error_message = exc.message
            return False
        else:
            self.errors = []
            self.has_error = False
            self.error_message = ""
            return True
        finally:
            if self._render_extra_validators:
                self.field.validators = saved  # type: ignore[possibly-undefined]

    # ── Reactive watchers ─────────────────────────────────────────────────────

    def watch_value(self, new_value: Any) -> None:
        """Sync inner widget when value is set programmatically."""
        if not self._from_widget and self._inner is not None:
            try:
                self._inner.value = self.field.to_widget(new_value)
            except Exception:
                pass
        if new_value != self._initial_value:
            self.is_dirty = True

    def watch_error_message(self, message: str) -> None:
        """Update the error label in the DOM."""
        try:
            error_label = self.query_one(".field-error", Static)
            error_label.update(message)
            error_label.display = bool(message)
        except Exception:
            pass  # not yet mounted — on_mount will sync

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_form_value_changed(self, event: FormValueChanged) -> None:
        """Receive value changes from the inner widget."""
        event.stop()
        self._from_widget = True
        try:
            self.value = self.field.to_python(event.value)
        finally:
            self._from_widget = False

    def on_form_blurred(self, event: FormBlurred) -> None:
        """Validate when inner widget loses focus."""
        event.stop()
        self.validate()

    # ── Textual widget lifecycle ──────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        label_style = self._effective_label_style()
        help_style = self._effective_help_style()

        # Merge widget kwargs: field defaults < call-site overrides.
        merged_kwargs: dict[str, Any] = {
            **self.field.widget_kwargs,
            **self._render_widget_kwargs,
        }

        # Resolve disabled state.
        is_disabled = (
            self._render_disabled
            if self._render_disabled is not None
            else self._disabled
        )
        if is_disabled:
            merged_kwargs["disabled"] = True

        # Placeholder style: inject label as widget placeholder.
        if label_style == "placeholder":
            merged_kwargs["placeholder"] = self.field.label

        # Instantiate inner widget.
        self._inner = self.field.widget_class(bound_field=self, **merged_kwargs)

        # Compose the label + widget structure.
        if label_style == "above":
            yield Label(self.field.label, classes="field-label")
            yield self._inner
        elif label_style == "beside":
            with Horizontal(classes="field-row"):
                yield Label(self.field.label, classes="field-label")
                yield self._inner
        else:  # "placeholder"
            yield self._inner

        # Help text.
        if self.field.help_text and help_style == "below":
            yield Static(self.field.help_text, classes="field-help")

        # Error display (hidden until validate() fires).
        error_label = Static("", classes="field-error")
        error_label.display = False
        yield error_label

    def on_mount(self) -> None:
        # Sync initial value to inner widget.
        if self._inner is not None and self._initial_value is not None:
            try:
                self._inner.value = self.field.to_widget(self._initial_value)
            except Exception:
                pass
        # Attach tooltip if help_style is "tooltip".
        if self.field.help_text and self._effective_help_style() == "tooltip":
            if self._inner is not None:
                self._inner.tooltip = self.field.help_text

    def __repr__(self) -> str:
        return (
            f"BoundField(name={self.name!r}, "
            f"field={self.field!r}, "
            f"value={self.value!r})"
        )
