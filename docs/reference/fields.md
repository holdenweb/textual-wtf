# Fields

Field classes are immutable declarative objects that define a form field's label, constraints, validators, and default widget. They live at class level on a `Form` subclass.

## Field (base class)

::: textual_wtf.fields.Field
    options:
      members:
        - __init__
        - bind
        - to_python
      show_root_heading: true
      show_source: false

### Common parameters

All field subclasses accept these keyword-only arguments (after the positional `label`):

`label: str`
:   The human-readable field label. Positional (first argument).

`initial: Any = None`
:   Default value when no `data=` is passed to the form constructor.

`required: bool = False`
:   When `True`, a `Required` validator is prepended and the field is **pinned** — the form-level required cascade cannot override it.

`disabled: bool = False`
:   Render the widget in a disabled state.

`validators: list | tuple = ()`
:   Additional validators. Plain callables are wrapped in `FunctionValidator` automatically.

`help_text: str = ""`
:   Descriptive text shown below or beside the input.

`label_style: LabelStyle | None = None`
:   Override the form-wide label style for this field.

`help_style: HelpStyle | None = None`
:   Override the form-wide help style for this field.

---

## StringField

::: textual_wtf.fields.StringField
    options:
      show_root_heading: true
      show_source: false

Single-line text input. Backed by `FormInput`.

```python
from textual_wtf import Form, StringField

class MyForm(Form):
    name = StringField(
        "Full name",
        required=True,
        min_length=2,
        max_length=100,
        help_text="First and last name.",
    )
```

### StringField parameters

`min_length: int | None = None`
:   Minimum character count. Adds a `MinLength` validator (fires on blur and submit).

`max_length: int | None = None`
:   Maximum character count. Adds a `MaxLength` validator (fires on every keystroke, blur, and submit).

---

## IntegerField

::: textual_wtf.fields.IntegerField
    options:
      show_root_heading: true
      show_source: false

Integer input. Backed by `FormInput` with a digit-only `restrict` pattern. `get_data()` returns `int | None`.

```python
from textual_wtf import Form, IntegerField

class AgeForm(Form):
    age = IntegerField("Age", minimum=0, maximum=150)
```

### IntegerField parameters

`minimum: int | None = None`
:   Inclusive lower bound. Adds a `MinValue` validator (fires on blur and submit).

`maximum: int | None = None`
:   Inclusive upper bound. Adds a `MaxValue` validator (fires on every keystroke, blur, and submit).

---

## BooleanField

::: textual_wtf.fields.BooleanField
    options:
      show_root_heading: true
      show_source: false

Boolean toggle. Backed by `FormCheckbox`. The `initial` value defaults to `False`.

```python
from textual_wtf import Form, BooleanField

class PrefsForm(Form):
    notifications = BooleanField("Enable notifications", initial=True)
    beta          = BooleanField("Opt in to beta", disabled=True)
```

---

## ChoiceField

::: textual_wtf.fields.ChoiceField
    options:
      show_root_heading: true
      show_source: false

Dropdown selection. Backed by `FormSelect`. Requires a non-empty `choices` list.

```python
from textual_wtf import Form, ChoiceField

SIZES = [("Small", "s"), ("Medium", "m"), ("Large", "l"), ("Extra large", "xl")]

class OrderForm(Form):
    size = ChoiceField("T-shirt size", choices=SIZES, required=True)
```

### ChoiceField parameters

`choices: list[tuple[str, Any]]`
:   A list of `(display_label, value)` pairs. An empty list raises `FieldError` immediately at class definition time.

---

## TextField

::: textual_wtf.fields.TextField
    options:
      show_root_heading: true
      show_source: false

Multi-line text area. Backed by `FormTextArea`.

```python
from textual_wtf import Form, TextField

class PostForm(Form):
    body = TextField(
        "Post body",
        min_length=10,
        max_length=5000,
        help_text="Markdown is supported.",
    )
```

### TextField parameters

`min_length: int | None = None`
:   Minimum character count. Adds a `MinLength` validator (fires on blur and submit).

`max_length: int | None = None`
:   Maximum character count. Adds a `MaxLength` validator (fires on every keystroke, blur, and submit).
