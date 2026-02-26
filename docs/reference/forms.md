# Forms

The form classes provide the declarative base for field definitions, the validation pipeline, and the data management API.

## BaseForm

::: textual_wtf.forms.BaseForm
    options:
      members:
        - layout_class
        - label_style
        - help_style
        - required
        - title
        - Submitted
        - Cancelled
        - __init__
        - bound_fields
        - fields
        - get_field
        - validate
        - is_valid
        - clean
        - clean_form
        - add_error
        - get_data
        - set_data
        - build_layout
      show_root_heading: true
      show_source: false

## Form

::: textual_wtf.forms.Form
    options:
      show_root_heading: true
      show_source: false
      docstring_section_style: table

---

## Class attribute reference

### layout_class

```python
layout_class: type[FormLayout] | None = None
```

The layout class used by `build_layout()`. When `None`, `DefaultFormLayout` is used. Set this on your form class to use a custom layout by default:

```python
class MyForm(Form):
    layout_class = MyTwoColumnLayout
```

### label_style

```python
label_style: LabelStyle = "above"
```

Default label positioning for all fields in this form. Fields that explicitly set their own `label_style` are not affected. Valid values:

- `"above"` — label on its own line above the input
- `"beside"` — label to the left of the input on the same line
- `"placeholder"` — label text used as the input placeholder; no visible label

### help_style

```python
help_style: HelpStyle = "below"
```

Default help-text rendering for all fields. Valid values:

- `"below"` — help text appears as a muted line below the input
- `"tooltip"` — help text appears in a tooltip on hover / focus

### required

```python
required: bool | None = None
```

Form-wide required default. `None` means "do not override field defaults". See the [required cascade](../guide/forms.md#the-required-cascade).

### title

```python
title: str = ""
```

Displayed as a bold heading at the top of `DefaultFormLayout`. Also used as the tab label in `TabbedForm`.

---

## Messages

### Form.Submitted

Posted when the user confirms the form and all validation passes.

```python
@dataclass
class Submitted(Message):
    layout: FormLayout   # the FormLayout widget that received the submit action
    form: BaseForm       # the form instance with validated data
```

Handle it anywhere in the widget hierarchy above the layout:

```python
@on(MyForm.Submitted)
def handle_submit(self, event: MyForm.Submitted) -> None:
    data = event.form.get_data()
```

### Form.Cancelled

Posted when the user presses Cancel or the Escape key.

```python
@dataclass
class Cancelled(Message):
    layout: FormLayout
    form: BaseForm
```

---

## Method reference

### __init__

```python
def __init__(
    self,
    data: dict[str, Any] | None = None,
    *,
    layout_class: type[FormLayout] | None = None,
    label_style: LabelStyle | None = None,
    help_style: HelpStyle | None = None,
    required: bool | None = None,
    title: str | None = None,
) -> None
```

All keyword arguments override the corresponding class attribute for this instance only.

### validate / is_valid

```python
def validate(self) -> bool
def is_valid(self) -> bool  # alias
```

Run all validators on every field. Returns `True` only if every field passes. Updates error state on failing `BoundField` objects. Does not call `clean_form()`.

### clean

```python
def clean(self) -> bool
```

Full pipeline: `validate()` then `clean_form()` (if all fields pass). Returns `True` only if both succeed. Synchronises error state to the UI after `clean_form()` completes.

### clean_form

```python
def clean_form(self) -> bool
```

Override in your form class for cross-field validation. Called only after `validate()` succeeds. Use `self.add_error()` to attach errors to specific fields. The base implementation returns `True`.

### add_error

```python
def add_error(self, field_name: str, message: str) -> None
```

Attach a validation error to the named field. Intended for use inside `clean_form()`. Raises `FormError` if `field_name` does not exist.

### get_data / set_data

```python
def get_data(self) -> dict[str, Any]
def set_data(self, data: dict[str, Any]) -> None
```

`get_data()` returns a snapshot of all current field values. `set_data()` updates the named fields without affecting others.

### build_layout

```python
def build_layout(self, id: str | None = None) -> FormLayout
```

Instantiate and return the form's layout widget. Uses `self._layout_class` (which defaults to `DefaultFormLayout`).
