"""BoundField — non-widget runtime adapter for one field within one form instance."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .controller import FieldController
from .exceptions import FormError, ValidationError
from .types import HelpStyle, LabelStyle
from .validators import FunctionValidator, Required, Validator

if TYPE_CHECKING:
    from textual.widget import Widget

    from .fields import Field
    from .forms import BaseForm


class BoundField:
    """Mutable runtime adapter for one field within one form instance.

    Created by ``Field.bind()`` during ``BaseForm.__init__``.  Not a Textual
    widget — it is a plain Python object that owns a :class:`FieldController`
    and knows how to produce either a raw inner widget (``__call__``) or a
    fully-composed ``FieldWidget`` (``simple_layout``).
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

        # Controller owns all mutable state / validation logic
        self.controller = FieldController(field, form, name, data or {})

        # Per-render style overrides
        self._label_style: LabelStyle = field.label_style
        self._help_style: HelpStyle = field.help_style
        self._widget_kwargs: dict[str, Any] = dict(field.widget_kwargs)
        self.disabled: bool = field.disabled

        # Render guard — set to True by __call__ or simple_layout
        self._rendered: bool = False

    # ── Properties delegated to Field (read-only) ────────────────

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

    # ── Value / error state (proxied to controller) ───────────────

    @property
    def value(self) -> Any:
        return self.controller.value

    @value.setter
    def value(self, new_value: Any) -> None:
        self.controller.value = new_value

    @property
    def is_dirty(self) -> bool:
        return self.controller.is_dirty

    @is_dirty.setter
    def is_dirty(self, v: bool) -> None:
        self.controller.is_dirty = v

    @property
    def errors(self) -> list[str]:
        return self.controller.errors

    @errors.setter
    def errors(self, v: list[str]) -> None:
        """Backward-compatible direct error assignment (use form.add_error() for new code)."""
        self.controller.errors = list(v)

    @property
    def has_error(self) -> bool:
        return self.controller.has_error

    @has_error.setter
    def has_error(self, v: bool) -> None:
        """Backward-compatible direct assignment (use form.add_error() for new code)."""
        self.controller.has_error = v

    @property
    def error_messages(self) -> list[str]:
        return self.controller.error_messages

    @error_messages.setter
    def error_messages(self, v: list[str]) -> None:
        """Backward-compatible direct assignment (use form.add_error() for new code)."""
        self.controller.error_messages = list(v)

    # ── Configuration ─────────────────────────────────────────────

    def _apply_required(self, required: bool) -> None:
        """Force-override the required state of this bound field.

        Unlike ``Field._with_required()``, this always applies regardless of
        whether the original field had ``required`` set explicitly.  It clones
        the field, updates the controller's reference, and is the correct path
        for render-level ``required=`` overrides (highest priority in the cascade).
        """
        import copy

        clone = copy.copy(self._field)
        clone.required = required
        clone.validators = [v for v in self._field.validators if not isinstance(v, Required)]
        if required:
            clone.validators.insert(0, Required())
        clone._required_explicitly_set = True
        self._field = clone
        self.controller._field = clone

    def _configure(
        self,
        *,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        disabled: bool | None = None,
        required: bool | None = None,
        **widget_kwargs: Any,
    ) -> None:
        """Apply per-render style and widget overrides."""
        if label_style is not None:
            self._label_style = label_style
        if help_style is not None:
            self._help_style = help_style
        if disabled is not None:
            self.disabled = disabled
        if required is not None:
            self._apply_required(required)
        self._widget_kwargs.update(widget_kwargs)

    def _check_not_rendered(self) -> None:
        if self._rendered:
            raise FormError(
                f"Field {self._name!r} has already been yielded in this layout."
            )
        self._rendered = True

    # ── Public rendering API ──────────────────────────────────────

    def __call__(
        self,
        *,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        disabled: bool | None = None,
        required: bool | None = None,
        **widget_kwargs: Any,
    ) -> Widget:
        """Return the raw inner widget (Input / Checkbox / Select / TextArea).

        The returned widget has ``._field_controller`` stamped on it so that
        a :class:`~textual_wtf.ControllerAwareLayout` ancestor can route
        Textual widget events back to the controller.

        Call this when you want full layout freedom — place the widget inside
        any Textual container you like.  Use ``simple_layout()`` when you
        want the bundled label + input + help + error chrome.
        """
        self._check_not_rendered()
        self._configure(
            label_style=label_style,
            help_style=help_style,
            disabled=disabled,
            required=required,
            **widget_kwargs,
        )
        widget = self._build_inner_widget()
        widget._field_controller = self.controller  # type: ignore[attr-defined]
        return widget

    def simple_layout(
        self,
        *,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        disabled: bool | None = None,
        required: bool | None = None,
        renderer: Any | None = None,
        **widget_kwargs: Any,
    ) -> Any:  # returns FieldWidget, typed as Any to avoid circular import
        """Return a :class:`~textual_wtf.FieldWidget` (label + input + help + error).

        This is the successor to the old ``__call__`` behaviour — yields a
        self-contained Textual Container that renders all field chrome.

        Pass ``renderer=callable`` to override the entire inner layout; the
        callable receives this ``BoundField`` and must return a
        ``ComposeResult``.
        """
        from .field_widget import FieldWidget

        self._check_not_rendered()
        self._configure(
            label_style=label_style,
            help_style=help_style,
            disabled=disabled,
            required=required,
            **widget_kwargs,
        )
        return FieldWidget(bound_field=self, renderer=renderer)

    # ── Validation (thin delegators) ──────────────────────────────

    def validate(self) -> bool:
        """Validate this field (submit path).  Fires error listeners."""
        return self.controller.validate()

    def _validate_for(self, event: str) -> bool:
        """Event-scoped validation.  Fires error listeners."""
        result = self.controller._validate_for(event)
        self.controller._notify_errors()
        return result

    # ── Inner widget construction ─────────────────────────────────

    def _build_inner_widget(self) -> Widget:
        """Instantiate the raw Textual input widget from Field configuration."""
        from .fields import BooleanField, ChoiceField
        from .widgets import FormTextArea

        from textual.widgets import TextArea

        widget_class = self._field.widget_class
        kwargs = dict(self._widget_kwargs)

        if isinstance(self._field, BooleanField):
            widget = widget_class(self.label, self.controller.value or False, **kwargs)
        elif isinstance(self._field, ChoiceField):
            options = list(self._field.choices)
            legal_values = {val for _, val in self._field.choices}
            val = self.controller.value
            if val in legal_values:
                widget = widget_class(options, value=val, **kwargs)
            else:
                widget = widget_class(options, allow_blank=True, **kwargs)
        elif widget_class in (FormTextArea, TextArea):
            widget = widget_class(**kwargs)
            val = self.controller.value
            widget.text = str(val) if val is not None else ""
        else:
            val = self.controller.value
            widget = widget_class(
                value=str(val) if val is not None else "",
                **kwargs,
            )

        widget.disabled = self.disabled
        return widget
