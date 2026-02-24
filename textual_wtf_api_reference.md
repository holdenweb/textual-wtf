# textual-wtf — Python API Reference

> **Status:** Design specification. Describes the target API. Still under development.

---

## Contents

1. [Field](#1-field)
2. [Field subclasses](#2-field-subclasses)
3. [BoundField](#3-boundfield)
4. [Form](#4-form)
5. [FormLayout](#5-formlayout)
6. [Validators](#6-validators)
7. [Exceptions](#7-exceptions)
8. [Constants and type aliases](#8-constants-and-type-aliases)

---

## 0. Introduction

This document describes the design of a forms suystem for Textual. The user begins
by declaring a Form subclass, in which Field and embedded Form instances are assigned to class
variables. The FormMetaclass extracts these Field definitions, saving them in the `fields`
class variable.

When a Form instance is created, each of the fields is bound to the new
instance as a BoundField. Thus the Field holds the configuration data for a
field, which is the same for all instances of that Form, while the BoundField
holds the field data for a specific Form instance.

## 1. `Field`

```python
class Field
```

Immutable declarative configuration for a single form field. Defined at class
level on a `Form` subclass and shared across all instances of that form.
Never holds runtime state.

### Constructor

```python
Field(
    label: str,
    *,
    initial: Any = None,
    required: bool = False,
    disabled: bool = False,
    validators: list[Validator | Callable] = (),
    help_text: str = "",
    label_style: LabelStyle = "above",
    help_style: HelpStyle = "below",
    widget_class: type | None = None,
    **widget_kwargs: Any,
)
```

| Parameter | Description |
|-----------|-------------|
| `label` | Human-readable label shown in the UI. |
| `label_style` | How the label is presented. One of `"above"`, `"beside"`, `"placeholder"`. See [Constants](#8-constants-and-type-aliases). |
| `help_style` | How help text is presented. One of `"below"`, `"tooltip"`. |
| `widget_class` | The Textual widget class to instantiate for this field. If `None`, the subclass default is used. |
| `**b_field_kwargs` | Additional keyword arguments forwarded to the BoundField constructor. Those not used by the BoundField are later merged with (and overridden by) any kwargs passed to `BoundField.__call__()` at render time. |

### Methods

#### `bind`

```python
def bind(
    self,
    form: BaseForm,
    name: str,
    initial: Any = None,
) -> BoundField
```

Returns a `BoundField` for this `Field` within a specific form instance.
Called by `BaseForm.__init__()` and collected in the BoundField's field
dictionary under the field's name; not normally called directly.

---

## 2. Field subclasses

All subclasses accept every parameter of `Field` in addition to their own.

### `StringField`

```python
class StringField(Field)
```

Single-line text. Default `widget_class`: `FormInput`.

No additional parameters.

---

### `IntegerField`

```python
class IntegerField(Field)
```

Integer numeric input. Default `widget_class`: `FormInput` with
`type="integer"` (blocks non-numeric keystrokes at the widget level).

| Extra parameter | Description |
|-----------------|-------------|
| `min_value: int \| None = None` | Minimum acceptable value. If set, a `MinValue` validator is added automatically. |
| `max_value: int \| None = None` | Maximum acceptable value. If set, a `MaxValue` validator is added automatically. |

---

### `BooleanField`

```python
class BooleanField(Field)
```

Boolean toggle. Default `widget_class`: `FormCheckbox`.

No additional parameters.

---

### `ChoiceField`

```python
class ChoiceField(Field)
```

Selection from a fixed list. Default `widget_class`: `FormSelect`.

| Extra parameter | Description |
|-----------------|-------------|
| `choices: list[tuple[str, Any]]` | **Required.** List of `(display_label, value)` pairs. |

---

### `TextField`

```python
class TextField(Field)
```

Multi-line text. Default `widget_class`: `FormTextArea`.

No additional parameters.

---

## 3. `BoundField`

```python
class BoundField(Vertical, FieldMixin)
```

Mutable runtime state for one field within one form instance. Also a
Textual `Vertical` container widget: when mounted, it composes its own
label, inner input widget, optional help text, and error display.

Created by `Field.bind()` during `BaseForm.__init__()`, which stores
them in the Form instances bound_fields attribute . Not instantiated
directly.

### Constructor

```python
BoundField(
    field: Field,
    form: BaseForm,
    name: str,
    initial: Any = None,
)
```

Not part of the public API; called only by `Field.bind()`.

### Reactive attributes

These are Textual `reactive` attributes. Watchers update the DOM
automatically.

| Attribute | Type | Description |
|-----------|------|-------------|
| `value` | `Any` | Current Python value. Setting it updates the inner widget; the inner widget's `watch_value` watcher keeps this in sync when the user types. |
| `has_error` | `bool` | `True` when the field has at least one validation error. |
| `error_messages` | list[`str`] | Error messages accumulated during validation. Displayed in the error label inside the widget tree. |

### Properties (some delegated to `Field`, read-only)

| Property | Type | Description |
|----------|------|-------------|
| `label` | `str` | Human-readable label. |
| `default` | `Any` | Default value from the `Field` declaration. |
| `required` | `bool` | Whether the field is required. |
| `help_text` | `str` | Help guidance string. |
| `label_style` | `LabelStyle` | How the label is presented; overridable per-call via `__call__`. |
| `help_style` | `HelpStyle` | How help text is presented; overridable per-call via `__call__`. |
| `validators` | `list` | Field-level validators from the `Field` declaration. |
| `field` | `Field` | The underlying shared `Field` configuration object. |
| `form` | `BaseForm` | The owning form instance. |
| `name` | `str` | The field name (its key in `form.bound_fields`). |

### Mutable instance attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `disabled` | `bool` | Independently mutable per instance. Initialised from `field.disabled`. Setting this updates the inner widget's disabled state. |
| `errors` | `list[str]` | Current validation error messages. Populated by `validate()`; cleared before each validation pass. |
| `is_dirty` | `bool` | `True` once the user has interacted with the field (changed its value from `initial`). |


Convert a Python value to the representation expected by the widget
(typically a string).

#### `validate`

```python
def validate(self, value: Any) -> None
```

Run all field-level validators against `value` (already converted via
`to_python`). Raises `ValidationError` on the first failure.

#### `clean`

```python
def clean(self, raw_value: Any) -> Any
```

Full field-level cleaning pipeline: call `to_python`, enforce `required`,
run `validate`. Returns the cleaned Python value, or raises
`ValidationError`. Called by `BoundField.validate()` on blur and by
`BaseForm.validate()` on submission.


### `__call__`

```python
def __call__(
    self,
    *,
    label_style: LabelStyle | None = None,
    help_style: HelpStyle | None = None,
    disabled: bool | None = None,
    validators: list | None = None,
    **widget_kwargs: Any,
) -> BoundField
```

Configure this `BoundField` for rendering and return a fully-configured widget. Used when
composing the BoundForm to yield the field into the widget tree.

Any keyword argument supplied here takes precedence over the corresponding
`Field` declaration. `widget_kwargs` are merged with (and override)
`field.widget_kwargs`.

Raises `FormError` if this field has already been yielded in the current
layout (duplicate-render protection).

```python
# Typical usage in compose_form():
yield self.form.name()                          # all defaults
yield self.form.age(disabled=True)              # disable for this render
yield self.form.role(label_style="beside")      # override label style
yield self.form.notes(help_style="tooltip")     # override help style
```

Returns `self` so that the yield expression is the `BoundField` widget
itself — Textual mounts it as a `Vertical` container.

### `to_python`

```python
def to_python(self, value: Any) -> Any
```

Convert a raw widget string value to the appropriate Python type.
Raises `ValidationError` if conversion fails (e.g. non-integer input for
`IntegerField`).

### `to_widget`

```python
def to_widget(self, value: Any) -> Any
```

Convert a Python value to the representation expected by the widget
(typically a string).

### `validate`

```python
def validate(self) -> bool
```

Run `field.clean(self.value)`. On success, clears `errors`, sets
`has_error = False`. On `ValidationError`, populates `errors` and
`error_message`, sets `has_error = True`.

Returns `True` if valid, `False` otherwise. Called automatically on blur
via the `on_blur` watcher; also called for every field by
`BaseForm.validate()` on submission.

### `compose` (Textual override)

```python
def compose(self) -> ComposeResult
```

Yields a FieldLayout object that contains the BoundField's widget subtree from the current `label_style` and `help_style`:

- `"above"`: `Label` stacked above the inner widget.
- `"beside"`: `Label` and inner widget in a `Horizontal`.
- `"placeholder"`: no `Label` widget; `field.label` passed as `placeholder`
  to the inner widget.

Help text: visible `Static` below the widget (`"below"`) or assigned to
`widget.tooltip` (`"tooltip"`).

Error display: a `Label` with reactive binding to `error_messages`, hidden
when `has_error` is `False`.

Not normally overridden; control presentation via `label_style` and
`help_style` instead.

---

## 4. `Form`

```python
class BaseForm
class Form(BaseForm)  # public alias
```

Declarative base class for form definitions. `FormMetaclass` processes the
class body at definition time.

### Class-level attributes (set on subclasses)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `layout_class` | `type[FormLayout] \| None` | `None` (→ `DefaultFormLayout`) | The `FormLayout` subclass used by `render()` when no `layout_class` is passed to the constructor. |
| `label_style` | `LabelStyle` | `"above"` | Default `label_style` for all fields in this form, unless overridden per-field in the `Field` declaration or per-render in `BoundField.__call__()`. |
| `help_style` | `HelpStyle` | `"below"` | Default `help_style` for all fields. |

### Constructor

```python
Form(
    data: dict[str, Any] | None = None,
    *,
    layout_class: type[FormLayout] | None = None,
    label_style: str | None = None,
)
```

| Parameter | Description |
|-----------|-------------|
| `data` | Optional initial data dict `{field_name: value}`. Values are applied as each `BoundField`'s initial `value`. |
| `layout_class` | Overrides `Form.layout_class` for this instance only. |
| `label_style` | Overrides `Form.;abel_style` for this instance only. |

### Field access

```python
form.fieldname          # returns BoundField; raises AttributeError if unknown
form.get_field(name)    # equivalent; kept for backward compatibility
form.bound_fields       # dict[str, BoundField], ordered by declaration
form.fields             # alias for bound_fields
```

For embedded forms, unqualified names (e.g. `form.street`) resolve when
unambiguous across all prefixed fields; raise `AmbiguousFieldError`
otherwise. Qualified names (e.g. `form.billing_street`) always resolve
directly.

### Methods

#### `bound_field`

```python
def bound_field(self, id: str | None = None) -> FormLayout
```

Instantiate and return the layout for this Form instance. Uses `self._layout_class`
(resolved from constructor arg → class attr → `DefaultFormLayout`).
The returned `FormLayout` is ready to mount in a Textual `compose()`.

#### `validate` / `is_valid`

```python
def validate(self) -> bool
def is_valid(self) -> bool   # alias
```

Call `bound_field.validate()` for every field. Return `True` only if all
fields are valid. Populates `BoundField.errors` for any failing fields.

#### `get_data`

```python
def get_data(self) -> dict[str, Any]
```

Return `{name: bound_field.value}` for all fields.

#### `set_data`

```python
def set_data(self, data: dict[str, Any]) -> None
```

Set `bound_field.value` for each key present in `data`. Keys not present
in the form are ignored.

### Class method

#### `embed`

```python
@classmethod
def embed(
    cls,
    prefix: str,
    title: str = "",
) -> ComposedForm
```

Return an `EmbeddedForm` marker for use inside another form class body.
`FormMetaclass` expands it in place, prefixing all field names with
`f"{prefix}_"`. Name collisions with existing fields raise `FormError`
at class-definition time.

```python
class OrderForm(Form):
    billing  = AddressForm.compose(prefix="billing")
    shipping = AddressForm.compose(prefix="shipping")
    notes    = TextField(label="Notes")
```

### Messages (Textual)

#### `Form.Submitted`

```python
@dataclass
class Form.Submitted(Message):
    layout: FormLayout    # the FormLayout that posted the message
    form: BaseForm        # convenience alias: layout.form
```

Posted when the user submits the form (Submit button or Enter key).

#### `Form.Cancelled`

```python
@dataclass
class Form.Cancelled(Message):
    layout: FormLayout
    form: BaseForm
```

Posted when the user cancels the form (Cancel button or Escape key).

---

## 5. `FormLayout`

```python
class FormLayout(VerticalScroll)
```

Base class for form renderers. Subclass and override `compose_form()` to
create custom layouts. The base class handles button events, keyboard
shortcuts, and duplicate-field protection.

### Constructor

```python
FormLayout(
    form: BaseForm,
    id: str | None = None,
    **kwargs: Any,
)
```

`**kwargs` are forwarded to `VerticalScroll`.

### Override in subclasses

#### `compose`

```python
def compose(self) -> ComposeResult
```

Define the form's visual structure. Yield `BoundField` widgets via the
callable interface, plus any other Textual widgets (buttons, labels,
containers) needed for the layout.

```python
class TwoColumnLayout(FormLayout):
    def compose_form(self):
        with Horizontal():
            yield self.form.first_name(label_style="above")
            yield self.form.last_name(label_style="above")
        yield self.form.email()
        yield self.form.notes(help_style="tooltip")
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```

Each `BoundField` may only be yielded once per layout; a second yield
raises `FormError`.


### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `form` | `BaseForm` | The form instance passed to the constructor. |

### Button and keyboard handling (base class behaviour)

The base class responds to:

- `Button` press with `id="submit"` → posts `Form.Submitted` (calls `form.validate()` first; only
  posts if valid).
- `Button` press with `id="cancel"` → posts `Form.Cancelled`.
- `Key("enter")` → triggers submit.
- `Key("escape")` → triggers cancel.

`DefaultFormLayout` also adds a form title (if `Form` has a `title`
attribute) and the Submit/Cancel buttons automatically, so `compose()`
in `DefaultFormLayout` subclasses need not yield buttons explicitly.

### `DefaultFormLayout`

```python
class DefaultFormLayout(FormLayout)
```

Renders all fields in declaration order with `label_style` and `help_style`
taken from the form's class-level defaults. Adds a title bar and
Submit/Cancel buttons. Equivalent to the old `RenderedForm` behaviour.

Used automatically by `Form.render()` when no `layout_class` is specified.

Not normally subclassed directly; for custom layouts, subclass `FormLayout`.

---

## 6. Validators

```python
class Validator(ABC)
```

Validators are subclasses of textual.validation.Validator, which thereby
inherit Validator's `success()` and `failure()` methods. Alternatively, any
callable with signature `(value: Any) -> None` that raises `ValidationError`
on failure may be used directly.

### `Validator.validate`

```python
@abstractmethod
def validate(self, value: Any) -> None
```

Return `self.success()` when validation succeeds, otherwise return
`self.failure(message)` where message explains the problem..

### Built-in validators

| Class | Parameters | Raises if… |
|-------|-----------|------------|
| `Required` | — | value is `None`, `""`, or empty sequence |
| `MinLength(n)` | `n: int` | `len(value) < n` |
| `MaxLength(n)` | `n: int` | `len(value) > n` |
| `MinValue(n)` | `n: int \| float` | `value < n` |
| `MaxValue(n)` | `n: int \| float` | `value > n` |
| `EmailValidator` | — | value does not match a valid email pattern |

---

## 7. Exceptions

| Exception | Raised when |
|-----------|-------------|
| `ValidationError(message)` | A validator or `Field.clean()` rejects a value. Carries `message: str`. |
| `FieldError(message)` | Field configuration is invalid (e.g. unknown parameter, bad `choices` format). |
| `FormError(message)` | Form definition or rendering error: name collision in composition, duplicate field render, or invalid `layout_class`. |
| `AmbiguousFieldError(name, candidates)` | Unqualified attribute access (`form.street`) matches more than one field across composed sub-forms. Carries `name: str` and `candidates: list[str]`. |

---

## 8. Constants and type aliases

```python
LabelStyle = Literal["above", "beside", "placeholder"]
HelpStyle  = Literal["below", "tooltip"]
```

| `LabelStyle` | Visual effect |
|-------------|---------------|
| `"above"` | `Label` widget rendered above the input. Default. |
| `"beside"` | `Label` widget rendered to the left of the input in a `Horizontal`. |
| `"placeholder"` | No `Label` widget; `field.label` used as the input's placeholder text. |

| `HelpStyle` | Visual effect |
|------------|---------------|
| `"below"` | `Static` help text always visible below the input. Default. |
| `"tooltip"` | Help text assigned to `widget.tooltip`; shown on hover. |

---

## Appendix: label_style × help_style combinations

| | `help_style="below"` | `help_style="tooltip"` |
|---|---|---|
| `label_style="above"` | Label above, help text below | Label above, help on hover |
| `label_style="beside"` | Label left, help text below | Label left, help on hover |
| `label_style="placeholder"` | Placeholder label, help text below | Placeholder label, help on hover |

