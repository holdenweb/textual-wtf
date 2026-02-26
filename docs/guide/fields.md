# Fields & Validators

Fields are immutable declarative objects that live at class level on a `Form` subclass. They describe what the field looks like, what its constraints are, and which widget renders it. At form instantiation time each field is bound to a [`BoundField`][textual_wtf.BoundField] that carries the mutable runtime state.

## Common parameters

Every field accepts these keyword-only arguments (after the positional `label`):

`initial: Any = None`
:   Default value shown when no `data=` is supplied to the form constructor.

`required: bool = False`
:   Whether the field must have a non-empty value. When `True`, a [`Required`][textual_wtf.Required] validator is prepended automatically. Setting this explicitly **pins** the value — the form-level cascade cannot override it.

`disabled: bool = False`
:   Render the underlying widget in a disabled state.

`validators: list | tuple = ()`
:   Additional validators to run. Accepts `Validator` instances or plain callables. Plain callables are wrapped in `FunctionValidator` automatically.

`help_text: str = ""`
:   Descriptive text shown below the input (or as a tooltip, depending on `help_style`).

`label_style: LabelStyle | None = None`
:   Override the form-wide label style for this field only.

`help_style: HelpStyle | None = None`
:   Override the form-wide help style for this field only.

Any additional keyword arguments are forwarded to the underlying Textual widget constructor (`**widget_kwargs`).

---

## StringField

Single-line text input. Backed by `FormInput` (a `textual.widgets.Input` subclass).

```python
from textual_wtf import Form, StringField

class ProfileForm(Form):
    username = StringField(
        "Username",
        required=True,
        min_length=3,
        max_length=20,
        help_text="Letters, numbers, and underscores only.",
    )
    bio_url = StringField(
        "Website",
        initial="https://",
        help_text="Your personal or company site.",
    )
```

`min_length: int | None = None`
:   Minimum number of characters. Enforced by `MinLength` validator (fires on blur and submit).

`max_length: int | None = None`
:   Maximum number of characters. Enforced by `MaxLength` validator (fires on every keystroke, blur, and submit).

---

## IntegerField

Integer input. Backs by `FormInput` with a `restrict` pattern that only allows digits and the minus sign.

```python
from textual_wtf import Form, IntegerField

class SurveyForm(Form):
    rating = IntegerField(
        "Rating",
        minimum=1,
        maximum=10,
        help_text="Score from 1 (poor) to 10 (excellent).",
    )
    year_born = IntegerField("Year of birth", minimum=1900, maximum=2010)
```

`minimum: int | None = None`
:   Inclusive lower bound. Enforced by `MinValue` (fires on blur and submit).

`maximum: int | None = None`
:   Inclusive upper bound. Enforced by `MaxValue` (fires on every keystroke, blur, and submit).

`get_data()` returns the value as `int | None`. An empty input produces `None`.

---

## BooleanField

Toggle checkbox. Backed by `FormCheckbox`. The `initial` value defaults to `False` unless explicitly overridden.

```python
from textual_wtf import Form, BooleanField

class PreferencesForm(Form):
    dark_mode      = BooleanField("Use dark mode")
    notifications  = BooleanField("Enable notifications", initial=True)
    beta_features  = BooleanField("Opt in to beta features", disabled=True)
```

`get_data()` returns `True` or `False`.

---

## ChoiceField

Dropdown selection. Backed by `FormSelect`. Requires at least one choice.

```python
from textual_wtf import Form, ChoiceField

COUNTRIES = [
    ("United Kingdom", "gb"),
    ("United States", "us"),
    ("Canada", "ca"),
    ("Australia", "au"),
]

class ShippingForm(Form):
    country = ChoiceField(
        "Country",
        choices=COUNTRIES,
        required=True,
    )
    priority = ChoiceField(
        "Shipping speed",
        choices=[
            ("Standard (3–5 days)", "standard"),
            ("Express (1–2 days)", "express"),
            ("Next day", "next_day"),
        ],
        initial="standard",
    )
```

`choices: list[tuple[str, Any]]`
:   A list of `(display_label, value)` pairs. The display label is shown in the dropdown; the value is what `get_data()` returns. Providing an empty list raises `FieldError` immediately.

---

## TextField

Multi-line text area. Backed by `FormTextArea` (a `textual.widgets.TextArea` subclass).

```python
from textual_wtf import Form, TextField

class ArticleForm(Form):
    content = TextField(
        "Body",
        min_length=50,
        max_length=10000,
        help_text="Markdown is supported.",
    )
    notes = TextField("Internal notes")
```

`min_length: int | None = None`
:   Minimum character count. `MinLength` validator fires on blur and submit.

`max_length: int | None = None`
:   Maximum character count. `MaxLength` validator fires on every keystroke, blur, and submit.

---

## Built-in validators

Validators live in `textual_wtf.validators` and are also importable from `textual_wtf` directly.

### Required

Passes if the value is not `None`, not an empty string, and not an empty collection.

```python
from textual_wtf import StringField, Required

# Equivalent ways to mark a field as required:
name = StringField("Name", required=True)           # shorthand
name = StringField("Name", validators=[Required()])  # explicit validator
```

Fires on: `blur`, `submit`.

### MinLength / MaxLength

```python
from textual_wtf import StringField

username = StringField("Username", min_length=3, max_length=30)

# Or pass validators directly for finer control:
from textual_wtf import MinLength, MaxLength
username = StringField("Username", validators=[MinLength(3), MaxLength(30)])
```

`MinLength(n)` fires on: `blur`, `submit`.
`MaxLength(n)` fires on: `change`, `blur`, `submit`.

### MinValue / MaxValue

```python
from textual_wtf import IntegerField

age = IntegerField("Age", minimum=0, maximum=120)

# Or explicitly:
from textual_wtf import MinValue, MaxValue
age = IntegerField("Age", validators=[MinValue(0), MaxValue(120)])
```

`MinValue(n)` fires on: `blur`, `submit`.
`MaxValue(n)` fires on: `change`, `blur`, `submit`.

### EmailValidator

```python
from textual_wtf import Form, StringField, EmailValidator

class ContactForm(Form):
    email = StringField(
        "Email",
        required=True,
        validators=[EmailValidator()],
    )
```

Checks that the value matches the pattern `user@domain.tld`. Skips validation if the field is empty (combine with `Required` when you need a non-empty email).

Fires on: `blur`, `submit`.

---

## Custom validators

### Inline with FunctionValidator

The simplest approach: pass a plain callable to `validators=`. It receives the field value and should raise `ValidationError` if the value is invalid.

```python title="inline_validator.py"
from textual_wtf import Form, StringField, ValidationError

def no_spaces(value: str) -> None:
    if value and " " in value:
        raise ValidationError("Usernames cannot contain spaces.")

def starts_with_letter(value: str) -> None:
    if value and not value[0].isalpha():
        raise ValidationError("Must start with a letter.")

class SignupForm(Form):
    username = StringField(
        "Username",
        required=True,
        validators=[no_spaces, starts_with_letter],
    )
```

Plain callables are automatically wrapped in [`FunctionValidator`][textual_wtf.validators.FunctionValidator], which fires on `blur` and `submit`.

### Subclassing Validator

For reusable validators, subclass [`Validator`][textual_wtf.Validator] and override `validate()`:

```python title="custom_validator.py"
from typing import Any
from textual.validation import ValidationResult
from textual_wtf import Validator, ValidationError

class StartsWithLetter(Validator):
    """Value must start with an ASCII letter."""

    def validate(self, value: Any) -> ValidationResult:
        if value and not str(value)[0].isalpha():
            return self.failure("Must start with a letter.")
        return self.success()
```

Use it like any built-in validator:

```python
from textual_wtf import Form, StringField

class SignupForm(Form):
    username = StringField(
        "Username",
        required=True,
        validators=[StartsWithLetter()],
    )
```

### Controlling when a validator fires

Every `Validator` has a `validate_on` class attribute — a `frozenset[str]` of event names. Override it to control firing timing:

```python title="custom_validator.py"
class StrictFormatValidator(Validator):
    # Fire on every keystroke, blur, and submit
    validate_on: frozenset[str] = frozenset({"change", "blur", "submit"})

    def validate(self, value: Any) -> ValidationResult:
        # ... your logic
        return self.success()
```

Or pass it at instantiation time:

```python
class MyForm(Form):
    code = StringField(
        "Code",
        validators=[
            FunctionValidator(
                my_check_fn,
                validate_on=frozenset({"change", "blur", "submit"}),
            )
        ],
    )
```

!!! tip "Performance tip"
    Keep `validate_on` as `{"blur", "submit"}` for expensive validators (network lookups, regex on large text). Reserve `"change"` for lightweight checks like `MaxLength` where instant feedback is important.
