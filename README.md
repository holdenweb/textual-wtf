# textual-wtf

Declarative forms library for [Textual](https://textual.textualize.io/) TUI applications.

This is a complete revision of the library to improve maintainability,
consistency and usability for developers. While still technically pre-release
you can now write code with reasonable confidence that it's not going to need
too many changes in the future.

## Major improvements in this release

### Decoupled Form class and instances from the widget hierarchy

Form instances are now properly constructed, creating a `BoundField`
for each `Field` in the class definition to hold the instance-specific
data and remove the confusing sharing of class attributes.
`BoundField` became a plain Python object rather than a Textual widget.
A separate `FieldController` now owns all mutable state (value, errors, dirty flag, listeners),
and a new `FieldWidget` (`Container`) handles the Textual-side composition.
This separation makes `BoundField` usable outside a mounted app — for testing and programmatic
validation — and eliminates the fragility of mixing reactive state with widget lifetime.

### `simple_layout()` / `__call__()` rendering split

`BoundField` now offers two rendering modes: `simple_layout()` returns a fully composed
`FieldWidget` (label + input + help + error chrome), while `__call__()` returns just the
raw inner widget for full layout freedom. Both accept per-render overrides for
`label_style`, `help_style`, `disabled`, and `required`.

### `label_style` and `help_style`

Three label modes (`"above"`, `"beside"`, `"placeholder"`) and two help-text modes
(`"below"`, `"tooltip"`) are configurable at form class, form instance, field, and
render-call levels.

### Unified validation on the Textual `Validator` pattern

Validators became proper `Validator` subclasses with `validate()` methods.
Convenience kwargs (`required=`, `min_length=`, `max_length=`, `min_value=`, `max_value=`)
were added to field constructors. Event-scoped validation (`validate_on`) lets validators
fire only on blur, change, or submit.

### Form instance embedding

`ComposedForm` markers replaced with direct assignment of `Form` instances as class
attributes, with a `required=` cascade: field-level explicit pin → form class attribute →
form instance kwarg → render kwarg.

### `TabbedForm` widget

A `Widget` taking sub-forms and rendering each in a `TabPane` via `TabbedContent`.
Tab labels turn `$error` colour when any field in that tab has a validation error.

### `title=` kwarg on `BaseForm`

Instance-level title override, used as the `TabbedForm` tab label and as a heading
in `DefaultFormLayout`.

### Example code and MkDocs documentation

A small multi-screen demo app and a complete MkDocs + Material docs site:
two guide sections (7 pages), API reference with mkdocstrings (7 pages), and
how-to recipes (4 pages).


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
    billing = AddressForm()
    shipping = AddressForm()
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
            self.add_error("confirm", "Passwords do not match")
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
            yield self.form.first_name.simple_layout(label_style="above")
            yield self.form.last_name.simple_layout(label_style="above")
        yield self.form.email.simple_layout()
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```
