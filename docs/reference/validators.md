# Validators

Validators check field values and produce pass/fail results. All textual-wtf validators subclass `textual_wtf.validators.Validator`, which itself subclasses Textual's `textual.validation.Validator`.

## Validator (base class)

::: textual_wtf.validators.Validator
    options:
      members:
        - validate_on
        - __init__
        - validate
      show_root_heading: true
      show_source: false

### validate_on

```python
validate_on: frozenset[str] = frozenset({"blur", "submit"})
```

The set of event names that trigger this validator during interactive use. Override at the class level or pass `validate_on=` to the constructor.

Valid event names:

- `"change"` — fires on every widget value change (keystroke, toggle, selection)
- `"blur"` — fires when focus leaves the widget
- `"submit"` — fires during `form.validate()` / `form.clean()`

!!! note "Submit always runs everything"
    `validate_on` only gates the interactive path. `form.validate()` runs every validator unconditionally.

---

## FunctionValidator

::: textual_wtf.validators.FunctionValidator
    options:
      members:
        - __init__
        - validate
      show_root_heading: true
      show_source: false

Wraps a plain callable as a `Validator`. The callable receives the field value; it should return normally on success or raise `ValidationError` on failure.

```python
from textual_wtf import ValidationError, FunctionValidator

def must_be_slug(value: str) -> None:
    if value and not value.replace("-", "").isalnum():
        raise ValidationError("Use only letters, numbers, and hyphens.")

slug_validator = FunctionValidator(must_be_slug)
```

Plain callables passed to `validators=` are wrapped in `FunctionValidator` automatically, so you rarely need to instantiate it directly.

---

## Required

::: textual_wtf.validators.Required
    options:
      show_root_heading: true
      show_source: false

Passes if the value is non-`None`, non-empty string (after stripping whitespace), and non-empty collection.

```python
from textual_wtf import Form, StringField, Required

class MyForm(Form):
    # Equivalent forms:
    name = StringField("Name", required=True)
    name = StringField("Name", validators=[Required()])
```

Fires on: `blur`, `submit`.

---

## MinLength

::: textual_wtf.validators.MinLength
    options:
      members:
        - __init__
        - validate
      show_root_heading: true
      show_source: false

Passes if `len(value) >= n`. Skips the check if `value` is `None`.

```python
from textual_wtf import Form, StringField, MinLength

class MyForm(Form):
    # Equivalent forms:
    bio = StringField("Bio", min_length=10)
    bio = StringField("Bio", validators=[MinLength(10)])
```

Fires on: `blur`, `submit`.

---

## MaxLength

::: textual_wtf.validators.MaxLength
    options:
      members:
        - __init__
        - validate
      show_root_heading: true
      show_source: false

Passes if `len(value) <= n`. Skips the check if `value` is `None`.

Fires on: `change`, `blur`, `submit` — giving instant feedback as the user types.

```python
from textual_wtf import Form, StringField, MaxLength

class MyForm(Form):
    # Equivalent forms:
    username = StringField("Username", max_length=30)
    username = StringField("Username", validators=[MaxLength(30)])
```

---

## MinValue

::: textual_wtf.validators.MinValue
    options:
      members:
        - __init__
        - validate
      show_root_heading: true
      show_source: false

Passes if `value >= n`. Skips if `value` is `None`.

```python
from textual_wtf import Form, IntegerField, MinValue

class ScoreForm(Form):
    # Equivalent forms:
    score = IntegerField("Score", minimum=0)
    score = IntegerField("Score", validators=[MinValue(0)])
```

Fires on: `blur`, `submit`.

---

## MaxValue

::: textual_wtf.validators.MaxValue
    options:
      members:
        - __init__
        - validate
      show_root_heading: true
      show_source: false

Passes if `value <= n`. Skips if `value` is `None`.

Fires on: `change`, `blur`, `submit`.

```python
from textual_wtf import Form, IntegerField, MaxValue

class BidForm(Form):
    amount = IntegerField("Bid amount", validators=[MaxValue(10000)])
```

---

## EmailValidator

::: textual_wtf.validators.EmailValidator
    options:
      show_root_heading: true
      show_source: false

Passes if the value matches a standard email pattern (`user@domain.tld`). Skips validation when the value is `None` or empty — combine with `Required` for a mandatory email field.

```python
from textual_wtf import Form, StringField, EmailValidator

class ContactForm(Form):
    email = StringField(
        "Email",
        required=True,
        validators=[EmailValidator()],
    )
```

Fires on: `blur`, `submit`.

---

## Writing a custom validator

Subclass `Validator` and override `validate()`. Use `self.success()` and `self.failure(message)` to return results:

```python title="custom_validator.py"
from typing import Any
from textual.validation import ValidationResult
from textual_wtf import Validator

class NoReservedWords(Validator):
    """Rejects usernames that are reserved system names."""

    RESERVED = frozenset({"admin", "root", "system", "superuser"})

    def validate(self, value: Any) -> ValidationResult:
        if isinstance(value, str) and value.lower() in self.RESERVED:
            return self.failure(
                f"{value!r} is a reserved name and cannot be used."
            )
        return self.success()
```

Use it on any field:

```python
from textual_wtf import Form, StringField

class SignupForm(Form):
    username = StringField(
        "Username",
        required=True,
        validators=[NoReservedWords()],
    )
```
