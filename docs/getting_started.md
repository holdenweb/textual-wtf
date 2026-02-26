# Getting Started

This page walks you through installing textual-wtf and building your first complete, working form from scratch.

## Installation

Install textual-wtf using your preferred package manager:

=== "uv"

    ```bash
    uv add textual-wtf
    ```

=== "pip"

    ```bash
    pip install textual-wtf
    ```

=== "poetry"

    ```bash
    poetry add textual-wtf
    ```

!!! note "Requirements"
    - Python 3.11 or later
    - Textual 1.0.0 or later

## Your first form

A form is a plain Python class that inherits from `Form`. Fields are declared as class attributes. The framework collects them in declaration order, preserves that order in the rendered layout, and manages all the runtime plumbing automatically.

```python title="contact_form.py"
from textual.app import App, ComposeResult, on
from textual_wtf import (
    Form,
    StringField,
    IntegerField,
    BooleanField,
    EmailValidator,
)


class ContactForm(Form):
    """A simple contact form with three fields."""

    title = "Contact Us"

    name = StringField(
        "Name",
        required=True,
        min_length=2,
        help_text="Enter your full name.",
    )
    age = IntegerField(
        "Age",
        minimum=0,
        maximum=120,
        help_text="Your age in years.",
    )
    newsletter = BooleanField(
        "Subscribe to the newsletter",
        help_text="We send updates monthly.",
    )
```

That's the entire form definition. No `__init__`, no widget IDs, no event wiring.

## Rendering the form

Call `form.build_layout()` inside your screen's `compose` method. It returns a `DefaultFormLayout` widget — a `VerticalScroll` container pre-populated with every field, a title label, and Submit / Cancel buttons.

```python title="contact_form.py (continued)"
class ContactApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    DefaultFormLayout {
        width: 60;
        max-height: 80%;
        border: solid $primary;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = ContactForm()
        yield self.form.build_layout()
```

!!! tip "Store the form instance"
    Keep a reference to the `ContactForm()` instance (`self.form`) so you can call `get_data()` after submission.

## Handling Submit and Cancel

`DefaultFormLayout` posts `Form.Submitted` when the user presses Submit (or Enter) and `Form.Cancelled` when they press Cancel (or Escape). Both messages bubble up to the screen.

```python title="contact_form.py (continued)"
    @on(ContactForm.Submitted)
    def on_submitted(self, event: ContactForm.Submitted) -> None:
        # event.form is the ContactForm instance
        data = event.form.get_data()
        # data = {"name": "Alice", "age": 30, "newsletter": True}
        self.notify(f"Submitted: {data}", severity="information")

    @on(ContactForm.Cancelled)
    def on_cancelled(self, event: ContactForm.Cancelled) -> None:
        self.notify("Cancelled", severity="warning")
        self.app.exit()
```

The `Submitted` message is posted **only** after all validators pass. If any field has a validation error, the layout highlights the problem and does not post the message — you never see invalid data in your handler.

!!! info "get_data() return type"
    `get_data()` returns a `dict[str, Any]` where each key is the field name (a string) and each value is the Python-typed result of the field's `to_python()` method. `IntegerField` values are `int | None`, `BooleanField` values are `bool`, and `StringField` values are `str | None`.

## Complete runnable example

Putting it all together:

```python title="contact_form.py"
from textual.app import App, ComposeResult, on
from textual_wtf import (
    Form,
    StringField,
    IntegerField,
    BooleanField,
    EmailValidator,
)


class ContactForm(Form):
    title = "Contact Us"

    name = StringField(
        "Name",
        required=True,
        min_length=2,
        help_text="Enter your full name.",
    )
    age = IntegerField(
        "Age",
        minimum=0,
        maximum=120,
        help_text="Your age in years.",
    )
    newsletter = BooleanField(
        "Subscribe to the newsletter",
    )


class ContactApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    DefaultFormLayout {
        width: 60;
        max-height: 80%;
        border: solid $primary;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = ContactForm()
        yield self.form.build_layout()

    @on(ContactForm.Submitted)
    def on_submitted(self, event: ContactForm.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"Hello, {data['name']}!", severity="information")

    @on(ContactForm.Cancelled)
    def on_cancelled(self, event: ContactForm.Cancelled) -> None:
        self.app.exit()


if __name__ == "__main__":
    ContactApp().run()
```

Run it with:

```bash
python contact_form.py
```

## Pre-populating with data

Pass a `data` dictionary to the form constructor to pre-populate field values. This is useful for edit screens where you are modifying an existing record.

```python
existing_record = {"name": "Alice", "age": 30, "newsletter": True}

self.form = ContactForm(data=existing_record)
yield self.form.build_layout()
```

Each key in the dictionary must match a field name. Keys that do not correspond to any field are silently ignored.

!!! tip "Updating values at runtime"
    Use `form.set_data({"name": "Bob", "age": 25})` to update field values after the form has already been composed. Only the named fields are updated; others are left unchanged.

## What's next

- [Guide: Forms](guide/forms.md) — class attributes, the required cascade, and data methods
- [Guide: Fields](guide/fields.md) — all field types and validator options
- [Guide: Layout](guide/layout.md) — rendering modes, label styles, and custom layouts
- [Guide: Validation](guide/validation.md) — when validation fires and cross-field logic
