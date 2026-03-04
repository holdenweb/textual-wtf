# textual-wtf

**Declarative, validated forms for [Textual](https://textual.textualize.io/) TUI applications.**

Write a Python class; get a fully-featured form — rendered, validated, and data-bound — with no boilerplate.

📖 **Full documentation, guides and API reference:** [holdenweb.com/textual-wtf](https://holdenweb.com/textual-wtf)

---

## Installation

```bash
pip install textual-wtf
```

## Try the demo

```bash
uvx textual-wtf                  # before installation
textual-wtf                      # if installed in an active venv
python -m textual_wtf.examples   # from a source checkout
```

---

## Quick start

Define a form class, call `.layout()` to render it, and handle the `Submitted` message:

```python
from textual.app import App, ComposeResult
from textual_wtf import Form, StringField, IntegerField, BooleanField
from textual_wtf.forms import BaseForm


class ContactForm(Form):
    name       = StringField("Name",  required=True, max_length=80)
    age        = IntegerField("Age",  min_value=0, max_value=150)
    newsletter = BooleanField("Subscribe to newsletter")


class MyApp(App):
    def compose(self) -> ComposeResult:
        self.form = ContactForm()
        yield self.form.layout()

    # Handler name comes from BaseForm.Submitted — Form inherits it unchanged.
    def on_base_form_submitted(self, event: BaseForm.Submitted) -> None:
        data = event.form.get_data()   # {"name": "…", "age": 42, "newsletter": False}
        self.notify(f"Received: {data}")

    def on_base_form_cancelled(self, event: BaseForm.Cancelled) -> None:
        self.exit()


if __name__ == "__main__":
    MyApp().run()
```

**Enter** submits; **Escape** cancels. Validation runs automatically: `required` fields
and range/length constraints are checked on blur and on submit, and any field with an
error displays its message directly beneath the input.

---

## Field types

| Class | Textual widget | Key kwargs |
|---|---|---|
| `StringField` | `Input` | `required`, `min_length`, `max_length` |
| `IntegerField` | `Input` (digits only) | `required`, `min_value`, `max_value` |
| `BooleanField` | `Checkbox` | — |
| `ChoiceField`  | `Select` | `choices` |
| `TextField`    | `TextArea` | `max_length` |

All fields accept `help_text=` and a `validators=` list.  Extra keyword arguments
are forwarded directly to the underlying Textual widget — for example
`StringField("Password", password=True)` gives you a masked input.

---

## Label and help-text styles

Control where labels and help text appear at form-class, form-instance, field, or
per-render-call level:

```python
class CompactForm(Form):
    label_style = "placeholder"   # "above" (default) | "beside" | "placeholder"
    help_style  = "tooltip"       # "below" (default) | "tooltip"

    username = StringField("Username", help_text="3–30 characters")
    email    = StringField("Email",    help_text="Used for notifications")
```

`"placeholder"` folds the label into the `Input` placeholder — saving a full row per
text field.  `"tooltip"` moves help text off the screen and onto a hover tooltip.

---

## Embedded sub-forms

Assign a `Form` instance as a class attribute and its fields are flattened into the
parent with a prefix:

```python
class AddressForm(Form):
    street = StringField("Street", required=True)
    city   = StringField("City",   required=True)


class OrderForm(Form):
    billing  = AddressForm()
    shipping = AddressForm(required=False)
    notes    = TextField("Notes")
```

Fields become `billing_street`, `billing_city`, `shipping_street`, … and
`get_data()` / `set_data()` work on the merged flat namespace.

---

## Cross-field validation

Override `clean_form()` for validation that spans more than one field:

```python
class PasswordChangeForm(Form):
    current = StringField("Current password", required=True, password=True)
    new     = StringField("New password",     required=True, password=True)
    confirm = StringField("Confirm",          required=True, password=True)

    def clean_form(self) -> bool:
        if self.new.value == self.current.value:
            self.add_error("new", "New password must differ from current")
            return False
        if self.new.value != self.confirm.value:
            self.add_error("confirm", "Passwords do not match")
            return False
        return True
```

`add_error(field_name, message)` attaches the error to the named field and marks it
visible in the UI.

---

## Multi-tab forms

```python
from textual_wtf import TabbedForm

class SettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield TabbedForm(ProfileForm(), PreferencesForm(), AccessibilityForm())
```

Tab labels turn red when a tab contains a validation error, guiding the user to the
problem without them having to click through every tab.

---

## Custom layouts

Subclass `ControllerAwareLayout` and override `compose()`.  Access the current form
as `self.form`; use `bf.simple_layout()` for the full label + input + error chrome,
or call `bf()` for the raw Textual widget alone:

```python
from textual.containers import Horizontal
from textual.widgets import Button
from textual_wtf import ControllerAwareLayout


class TwoColumnLayout(ControllerAwareLayout):
    def compose(self):
        with Horizontal():
            yield self.form.first_name.simple_layout()
            yield self.form.last_name.simple_layout()
        yield self.form.email.simple_layout()
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```

---

## Custom validators

Subclass `Validator` and raise `ValidationError` when the value is invalid:

```python
from textual_wtf.validators import Validator, ValidationError


class StrongPassword(Validator):
    def validate(self, value: str) -> None:
        if not any(c.isdigit() for c in value):
            raise ValidationError("Must contain at least one digit")
        if not any(c.isupper() for c in value):
            raise ValidationError("Must contain at least one uppercase letter")


class SignupForm(Form):
    password = StringField("Password", required=True,
                           validators=[StrongPassword()])
```

Plain functions also work — wrap them in `validators=[my_function]` and they are
promoted to `FunctionValidator` automatically.

---

## Development setup

```bash
git clone https://github.com/holdenweb/textual-wtf
cd textual-wtf
uv sync
uv run pytest
```

---

📖 **Guides · API reference · how-to recipes:** [holdenweb.com/textual-wtf](https://holdenweb.com/textual-wtf)
