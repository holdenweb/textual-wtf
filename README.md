# textual-wtf

Declarative forms library for [Textual](https://textual.textualize.io/) TUI applications.

## Installation

```bash
uv sync
```

## Running tests

```bash
uv run pytest -v
```

## Quick start

```python
from textual.app import App, ComposeResult
from textual_wtf import Form, StringField, IntegerField, BooleanField
from textual_wtf.forms import BaseForm


class ContactForm(Form):
    title = "Contact"
    name = StringField("Name", required=True)
    age = IntegerField("Age", min_value=0, max_value=150)
    active = BooleanField("Active")


class MyApp(App):
    def compose(self) -> ComposeResult:
        self.form = ContactForm()
        yield self.form.build_layout()

    def on_base_form_submitted(self, event: BaseForm.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"Submitted: {data}")

    def on_base_form_cancelled(self, event: BaseForm.Cancelled) -> None:
        self.exit()


if __name__ == "__main__":
    MyApp().run()
```

## Embedded forms

```python
class AddressForm(Form):
    street = StringField("Street")
    city = StringField("City")

class OrderForm(Form):
    billing = AddressForm.embed(prefix="billing")
    shipping = AddressForm.embed(prefix="shipping")
    notes = TextField("Notes")
```

## Cross-field validation

Override `clean_form()` for validation that spans multiple fields:

```python
class PasswordForm(Form):
    password = StringField("Password", required=True)
    confirm = StringField("Confirm", required=True)

    def clean_form(self):
        if self.password.value != self.confirm.value:
            self.confirm.errors = ["Passwords do not match"]
            self.confirm.has_error = True
            return False
        return True
```

## Custom layouts

Subclass `FormLayout` and override `compose()`:

```python
from textual.containers import Horizontal
from textual.widgets import Button
from textual_wtf import FormLayout

class TwoColumnLayout(FormLayout):
    def compose(self):
        with Horizontal():
            yield self.form.first_name(label_style="above")
            yield self.form.last_name(label_style="above")
        yield self.form.email()
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```
