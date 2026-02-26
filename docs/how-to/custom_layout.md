# How-to: Build a Custom Two-Column Layout

This guide shows how to arrange form fields in two equal columns using a custom layout class that extends `ControllerAwareLayout`.

## Goal

Given a form with six fields, render them in a two-column grid with Submit and Cancel buttons spanning the full width at the bottom.

```
┌─────────────────────┬─────────────────────┐
│  First name         │  Last name          │
│  [              ]   │  [              ]   │
│  Email              │  Phone              │
│  [              ]   │  [              ]   │
│  Company            │  Job title          │
│  [              ]   │  [              ]   │
├─────────────────────┴─────────────────────┤
│  [Submit]  [Cancel]                       │
└───────────────────────────────────────────┘
```

## The form

```python title="two_column_demo.py"
from textual_wtf import Form, StringField

class ContactForm(Form):
    title = "New Contact"

    first_name = StringField("First name", required=True)
    last_name  = StringField("Last name", required=True)
    email      = StringField("Email", required=True)
    phone      = StringField("Phone")
    company    = StringField("Company")
    job_title  = StringField("Job title")
```

## The custom layout

Subclass `ControllerAwareLayout` and implement `compose()`. Use `self.form.bound_fields` to access all bound fields in declaration order, then split them into two columns.

```python title="two_column_demo.py"
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label
from textual_wtf import ControllerAwareLayout

class TwoColumnLayout(ControllerAwareLayout):
    """Arrange fields in a two-column grid."""

    DEFAULT_CSS = """
    TwoColumnLayout {
        height: auto;
        padding: 1 2;
    }
    TwoColumnLayout .form-title {
        text-style: bold;
        margin-bottom: 1;
    }
    TwoColumnLayout .column {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }
    TwoColumnLayout #buttons {
        height: auto;
        margin-top: 1;
    }
    TwoColumnLayout #buttons Button {
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        # Optional title
        title = getattr(self.form, "title", "")
        if title:
            yield Label(title, classes="form-title")

        # Split fields into two columns (even-indexed → left, odd-indexed → right)
        all_fields = list(self.form.bound_fields.values())
        left_fields  = all_fields[::2]   # 0, 2, 4, …
        right_fields = all_fields[1::2]  # 1, 3, 5, …

        with Horizontal():
            with Vertical(classes="column"):
                for bf in left_fields:
                    yield bf.simple_layout()

            with Vertical(classes="column"):
                for bf in right_fields:
                    yield bf.simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```

## Wiring it up

Assign the custom layout class to the form:

```python title="two_column_demo.py"
class ContactForm(Form):
    layout_class = TwoColumnLayout   # ← use our layout
    title        = "New Contact"

    first_name = StringField("First name", required=True)
    last_name  = StringField("Last name", required=True)
    email      = StringField("Email", required=True)
    phone      = StringField("Phone")
    company    = StringField("Company")
    job_title  = StringField("Job title")
```

## The full app

```python title="two_column_demo.py"
from textual.app import App, ComposeResult, on
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label
from textual_wtf import Form, StringField, ControllerAwareLayout


class TwoColumnLayout(ControllerAwareLayout):
    DEFAULT_CSS = """
    TwoColumnLayout {
        height: auto;
        padding: 1 2;
    }
    TwoColumnLayout .form-title {
        text-style: bold;
        margin-bottom: 1;
    }
    TwoColumnLayout .column {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }
    TwoColumnLayout #buttons {
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        title = getattr(self.form, "title", "")
        if title:
            yield Label(title, classes="form-title")

        all_fields   = list(self.form.bound_fields.values())
        left_fields  = all_fields[::2]
        right_fields = all_fields[1::2]

        with Horizontal():
            with Vertical(classes="column"):
                for bf in left_fields:
                    yield bf.simple_layout()
            with Vertical(classes="column"):
                for bf in right_fields:
                    yield bf.simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")


class ContactForm(Form):
    layout_class = TwoColumnLayout
    title        = "New Contact"

    first_name = StringField("First name", required=True)
    last_name  = StringField("Last name", required=True)
    email      = StringField("Email", required=True)
    phone      = StringField("Phone")
    company    = StringField("Company")
    job_title  = StringField("Job title")


class ContactApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    TwoColumnLayout {
        width: 80;
        border: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = ContactForm()
        yield self.form.build_layout()

    @on(ContactForm.Submitted)
    def on_submitted(self, event: ContactForm.Submitted) -> None:
        data = event.form.get_data()
        self.notify(
            f"Saved contact: {data['first_name']} {data['last_name']}",
            severity="information",
        )

    @on(ContactForm.Cancelled)
    def on_cancelled(self, event: ContactForm.Cancelled) -> None:
        self.app.exit()


if __name__ == "__main__":
    ContactApp().run()
```

## Tips

!!! tip "Odd number of fields"
    If the form has an odd number of fields, `left_fields` will have one more field than `right_fields`. The right column will simply have an empty slot at the bottom. This is handled naturally by the list slicing.

!!! tip "Label style in two-column layouts"
    Consider using `label_style = "above"` (the default) or `label_style = "beside"` on the form. `"beside"` can make columns feel cramped at narrow widths; `"above"` generally works better in column arrangements.

!!! tip "Using bf() instead of simple_layout()"
    If you need complete control over individual field layout (for instance, to place the label and input in separate CSS grid cells), use `bf()` to get the raw widget. Since `TwoColumnLayout` extends `ControllerAwareLayout`, event routing to the controllers is handled automatically.
