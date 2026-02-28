# textual-wtf

**Declarative, validated forms for Textual TUI applications.**

textual-wtf brings the ergonomics of Django forms to the terminal. Define your form fields as class attributes, compose them into a layout in one line, and get real-time validation, embedded sub-forms, and tabbed multi-form support — all without writing boilerplate widget code.

<div class="grid cards" markdown>

-   **Declarative API**

    ---

    Define fields as class attributes on a `Form` subclass. Field order is preserved. No metaclass magic to wrestle with — it just works.

    ```python
    class SignupForm(Form):
        username = StringField("Username", required=True)
        email    = StringField("Email", validators=[EmailValidator()])
        age      = IntegerField("Age", minimum=18)
    ```

-   **Three-level required cascade**

    ---

    Control required state at the field, class, instance, or render level. Each level overrides the previous, giving you fine-grained control when embedding sub-forms.

    [:octicons-arrow-right-24: Required cascade](guide/forms.md#the-required-cascade)

-   **Embedded sub-forms**

    ---

    Assign a `Form` instance as a class attribute. Its fields are flattened into the parent with a name prefix (`billing_street`, `billing_city`, …). Required state cascades independently per embedding.

    [:octicons-arrow-right-24: Embedding guide](guide/embedding.md)

-   **Tabbed multi-form layout**

    ---

    `TabbedForm` renders multiple forms as tabs. Tab labels turn red whenever any field in that tab has a validation error, giving the user instant visual feedback.

    [:octicons-arrow-right-24: Tabbed forms](guide/tabbed_forms.md)

-   **Real-time validation**

    ---

    Validators fire on the right events automatically. `MaxLength` fires on every keystroke; `Required` fires on blur and submit. Custom validators are one function or one class away.

    [:octicons-arrow-right-24: Validation guide](guide/validation.md)

-   **Flexible rendering**

    ---

    Use `layout()` for a zero-config layout, `simple_layout()` for full chrome on each field, or `bf()` for the raw widget when you need complete layout freedom.

    [:octicons-arrow-right-24: Layout guide](guide/layout.md)

</div>

## At a glance

```python title="contact_form.py"
from textual.app import App, ComposeResult, on
from textual_wtf import Form, StringField, IntegerField, BooleanField
from textual_wtf import EmailValidator

class ContactForm(Form):
    title = "Contact Us"

    name    = StringField("Name", required=True, min_length=2)
    email   = StringField("Email", required=True, validators=[EmailValidator()])
    age     = IntegerField("Age", minimum=0, maximum=120)
    updates = BooleanField("Subscribe to updates")


class ContactApp(App):
    def compose(self) -> ComposeResult:
        self.form = ContactForm()
        yield self.form.layout()

    @on(ContactForm.Submitted)
    def on_submitted(self, event: ContactForm.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"Submitted: {data}")

    @on(ContactForm.Cancelled)
    def on_cancelled(self, event: ContactForm.Cancelled) -> None:
        self.app.exit()


if __name__ == "__main__":
    ContactApp().run()
```

## Installation

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

!!! note "Python version"
    textual-wtf requires Python 3.11 or later and Textual 1.0.0 or later.

## Where to go next

| Resource | What you'll find |
|---|---|
| [Getting Started](getting_started.md) | Step-by-step first form, submit/cancel handling |
| [Guide: Forms](guide/forms.md) | Class attributes, required cascade, data access |
| [Guide: Fields](guide/fields.md) | All field types and validators |
| [Guide: Layout](guide/layout.md) | Rendering modes and custom layouts |
| [Guide: Embedding](guide/embedding.md) | Sub-form embedding and field prefixes |
| [Guide: Validation](guide/validation.md) | When validation fires, cross-field logic |
| [Guide: Tabbed Forms](guide/tabbed_forms.md) | Multi-form tab layouts |
| [API Reference](reference/index.md) | Complete API documentation |
