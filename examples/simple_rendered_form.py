"""
Simplest possible form example for textual-wtf 0.9.x.

Demonstrates:
- Form.layout() with the built-in DefaultFormLayout
- Submitted / Cancelled message handling via @on decorator

Run with: python -m examples  (select "Simple Rendered Form")
"""

from textual.app import ComposeResult, on

from .example_screen import ExampleScreen
from textual_wtf import Form, StringField, IntegerField


class UserForm(Form):
    """Simple user registration form."""

    title = "User Registration"

    name = StringField(
        label="Name",
        required=True,
        min_length=3,
        help_text="Enter your full name",
    )
    age = IntegerField(
        label="Age",
        minimum=0,
        maximum=130,
        help_text="Enter your age in years",
    )


class SimpleRenderedFormScreen(ExampleScreen):
    """Minimal screen that displays a form via layout()."""

    CSS = """
    FormLayout {
        width: 60;
        max-height: 80%;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = UserForm()
        yield from self.form.layout()

    @on(Form.Submitted)
    def on_submitted(self, event: Form.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"Form submitted: {data}", severity="information")

    @on(Form.Cancelled)
    def on_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Form cancelled", severity="warning")
        self.action_back()
