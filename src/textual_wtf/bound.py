"""BoundField — non-widget runtime adapter for one field within one form instance."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from .controller import FieldController
from .exceptions import FormError
from .types import HelpStyle, LabelStyle

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widget import Widget

    from .fields import Field
    from .forms import BaseForm
    from .validators import Validator


class BoundField:
    """Runtime adapter for one field within one form instance.

    Created by ``Field.bind()`` during ``BaseForm.__init__``.  Not a Textual
    widget — it is a plain Python object that owns a :class:`FieldController`
    and knows how to produce either a raw inner widget (``__call__``) or a
    fully-composed ``FieldWidget`` (``simple_layout``).

    ``_label_style`` and ``_help_style`` are resolved once at bind time
    (field-explicit > form default) and are immutable thereafter.  Any
    per-render overrides are computed inline by ``simple_layout`` /
    ``__call__`` and passed directly to the widget — they are never stored
    here.
    """

    def __init__(
        self,
        field: Field,
        form: BaseForm,
        name: str,
        data: dict[str, Any] | None = None,
        *,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
    ) -> None:
        self._field = field
        self._form = form
        self._name = name

        # Controller owns all mutable state / validation logic, including the
        # render-consumed guard.
        self.controller = FieldController(field, form, name, data or {})

        # Bind-time resolved style defaults:
        #   field-explicit value > form-level default (passed in from BaseForm)
        self._label_style: LabelStyle = (
            label_style if label_style is not None else field.label_style
        )
        self._help_style: HelpStyle = (
            help_style if help_style is not None else field.help_style
        )

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
        """Bind-time resolved label style (field explicit > form default)."""
        return self._label_style

    @property
    def help_style(self) -> HelpStyle:
        """Bind-time resolved help style (field explicit > form default)."""
        return self._help_style

    @property
    def disabled(self) -> bool:
        """Field-level disabled flag (field definition default)."""
        return self._field.disabled

    @property
    def validators(self) -> list[Validator]:
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

    @property
    def has_error(self) -> bool:
        return self.controller.has_error

    @property
    def error_messages(self) -> list[str]:
        return self.controller.error_messages

    # ── Public rendering API ──────────────────────────────────────

    def __call__(
        self,
        *,
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
        self.controller.claim()
        if required is not None:
            self.controller.apply_required(required)

        effective_disabled = disabled if disabled is not None else self._field.disabled
        effective_kwargs: dict[str, Any] = {**self._field.widget_kwargs, **widget_kwargs}

        widget = self._build_inner_widget(
            disabled=effective_disabled,
            widget_kwargs=effective_kwargs,
        )
        widget._field_controller = self.controller  # type: ignore[attr-defined]
        return widget

    def simple_layout(
        self,
        *,
        label_style: LabelStyle | None = None,
        help_style: HelpStyle | None = None,
        disabled: bool | None = None,
        required: bool | None = None,
        renderer: Callable[[BoundField], ComposeResult] | None = None,
        **widget_kwargs: Any,
    ) -> Any:  # returns FieldWidget, typed as Any to avoid circular import
        """Return a :class:`~textual_wtf.FieldWidget` (label + input + help + error).

        Render options are resolved fresh on each call:
        call-site kwarg > bind-time default (form cascade > field explicit).
        Nothing is stored on this ``BoundField``; all resolved values are
        passed directly into the ``FieldWidget``.

        Pass ``renderer=callable`` to override the entire inner layout; the
        callable receives this ``BoundField`` and must return a
        ``ComposeResult``.
        """
        from .field_widget import FieldWidget

        self.controller.claim()
        if required is not None:
            self.controller.apply_required(required)

        effective_label_style: LabelStyle = (
            label_style if label_style is not None else self._label_style
        )
        effective_help_style: HelpStyle = (
            help_style if help_style is not None else self._help_style
        )
        effective_disabled = disabled if disabled is not None else self._field.disabled
        effective_kwargs: dict[str, Any] = {**self._field.widget_kwargs, **widget_kwargs}

        return FieldWidget(
            bound_field=self,
            label_style=effective_label_style,
            help_style=effective_help_style,
            disabled=effective_disabled,
            widget_kwargs=effective_kwargs,
            renderer=renderer,
        )

    # ── Validation (thin delegators) ──────────────────────────────

    def validate(self) -> bool:
        """Validate this field (submit path).  Fires error listeners."""
        return self.controller.validate()

    # ── Inner widget construction ─────────────────────────────────

    def _build_inner_widget(
        self,
        *,
        disabled: bool = False,
        widget_kwargs: dict[str, Any] | None = None,
    ) -> Widget:
        """Instantiate the raw Textual input widget from Field configuration."""
        from .fields import BooleanField, ChoiceField
        from .widgets import FormTextArea

        from textual.widgets import TextArea

        widget_class = self._field.widget_class
        # Always start from field-level widget_kwargs so field-level defaults
        # (e.g. IntegerField's restrict= pattern) are preserved even when this
        # method is called with no explicit widget_kwargs (e.g. from a renderer=
        # callback).  Call-site kwargs are merged on top and win on collision.
        kwargs = {**self._field.widget_kwargs, **(widget_kwargs or {})}

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

        widget.disabled = disabled
        return widget
