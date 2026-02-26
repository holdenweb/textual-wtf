# How-to: Write Custom Validators

There are two ways to add custom validation logic to a field: an inline function with `FunctionValidator`, or a reusable class by subclassing `Validator`.

## Approach 1: Inline function

For simple, one-off checks, pass a plain function to `validators=`. The function receives the field value and should raise `ValidationError` if the value is invalid. It should return `None` on success.

```python title="inline_validator.py"
from textual_wtf import Form, StringField, ValidationError


def no_spaces(value: str) -> None:
    """Reject values containing spaces."""
    if value and " " in value:
        raise ValidationError("Spaces are not allowed.")


def starts_with_letter(value: str) -> None:
    """Require the first character to be an ASCII letter."""
    if value and not value[0].isalpha():
        raise ValidationError("Must start with a letter (a–z or A–Z).")


class SignupForm(Form):
    username = StringField(
        "Username",
        required=True,
        min_length=3,
        max_length=20,
        validators=[no_spaces, starts_with_letter],
        help_text="Letters, digits, and underscores only. Must start with a letter.",
    )
```

Plain callables are wrapped in `FunctionValidator` automatically, so they fire on `blur` and `submit` by default.

!!! tip "Validation order"
    Validators run in the order they appear in the `validators` list. The `Required` validator (added by `required=True`) is always prepended first. Once one validator fails, the remaining validators in the list still run — all errors are collected.

    Wait — actually textual-wtf runs them all and collects all errors, so you may see multiple messages simultaneously.

## Approach 2: Reusable Validator subclass

For logic you want to reuse across multiple fields or forms, subclass `Validator` and override `validate()`:

```python title="validators.py"
from typing import Any
from textual.validation import ValidationResult
from textual_wtf import Validator, ValidationError


class SlugValidator(Validator):
    """Value must be a URL-safe slug: lowercase letters, digits, and hyphens.

    Leading and trailing hyphens are rejected.
    """

    def validate(self, value: Any) -> ValidationResult:
        if value is None or value == "":
            return self.success()  # let Required handle empty values

        s = str(value)
        if not s.replace("-", "").isalnum():
            return self.failure(
                "Slugs may only contain lowercase letters, digits, and hyphens."
            )
        if s != s.lower():
            return self.failure("Slugs must be all lowercase.")
        if s.startswith("-") or s.endswith("-"):
            return self.failure("Slugs cannot start or end with a hyphen.")

        return self.success()
```

Use it on any field:

```python title="post_form.py"
from textual_wtf import Form, StringField
from .validators import SlugValidator


class BlogPostForm(Form):
    title = StringField("Title", required=True)
    slug  = StringField(
        "Slug",
        required=True,
        max_length=100,
        validators=[SlugValidator()],
        help_text="URL-safe identifier, e.g. my-blog-post.",
    )
```

## Controlling when validation fires

By default, validators fire on `blur` and `submit`. To fire on every keystroke instead, override `validate_on`:

```python title="validators.py"
class MaxWordsValidator(Validator):
    """Limit the number of whitespace-separated words."""

    # Fire on every keystroke so the count stays live
    validate_on: frozenset[str] = frozenset({"change", "blur", "submit"})

    def __init__(self, max_words: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_words = max_words

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return self.success()
        count = len(str(value).split())
        if count > self.max_words:
            return self.failure(
                f"Too many words: {count} (maximum {self.max_words})."
            )
        return self.success()
```

```python title="post_form.py"
class BlogPostForm(Form):
    summary = StringField(
        "Summary",
        required=True,
        max_length=300,
        validators=[MaxWordsValidator(50)],
        help_text="Up to 50 words.",
    )
```

## Passing custom failure messages at instantiation

The base `Validator.__init__` accepts a `failure_description` positional argument. Your subclass can expose a configurable message:

```python title="validators.py"
class ProhibitedWordValidator(Validator):
    """Reject values that contain any word from a prohibited list."""

    def __init__(
        self,
        prohibited: list[str],
        *,
        validate_on: frozenset[str] | None = None,
    ) -> None:
        super().__init__(validate_on=validate_on)
        self._prohibited = [w.lower() for w in prohibited]

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return self.success()
        lower = str(value).lower()
        for word in self._prohibited:
            if word in lower:
                return self.failure(f"The word {word!r} is not allowed.")
        return self.success()
```

```python
class CommentForm(Form):
    body = TextField(
        "Comment",
        required=True,
        validators=[
            ProhibitedWordValidator(["spam", "advertisement", "click here"]),
        ],
    )
```

## Complete example

```python title="custom_validator_example.py"
from typing import Any
from textual.app import App, ComposeResult, on
from textual.validation import ValidationResult
from textual_wtf import (
    Form,
    StringField,
    IntegerField,
    Validator,
    ValidationError,
    ControllerAwareLayout,
)
from textual.containers import Horizontal
from textual.widgets import Button


class EvenNumberValidator(Validator):
    """Require an even integer."""

    def validate(self, value: Any) -> ValidationResult:
        if value is not None and int(value) % 2 != 0:
            return self.failure("Must be an even number.")
        return self.success()


def positive_or_none(value: Any) -> None:
    """Reject negative numbers."""
    if value is not None and value < 0:
        raise ValidationError("Must be a positive number or zero.")


class NumberForm(Form):
    even_count = IntegerField(
        "Even count",
        required=True,
        validators=[EvenNumberValidator()],
        help_text="Enter an even whole number.",
    )
    offset = IntegerField(
        "Offset",
        validators=[positive_or_none],
        help_text="Non-negative offset (optional).",
    )


class NumberApp(App):
    def compose(self) -> ComposeResult:
        self.form = NumberForm()
        yield self.form.build_layout()

    @on(NumberForm.Submitted)
    def on_submitted(self, event: NumberForm.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"count={data['even_count']}, offset={data['offset']}")


if __name__ == "__main__":
    NumberApp().run()
```
