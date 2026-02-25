"""
Simplest possible form example for textual-wtf 0.9.x.

Demonstrates:
- Form.render() with the built-in DefaultFormLayout
- Submitted / Cancelled message handling via @on decorator

Run with: python examples/simple_rendered_form.py
"""

from textual.app import ComposeResult, on
from example_app import ExampleApp
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


class FormApp(ExampleApp):
    """Minimal app that displays a form."""

    CSS = """
    FormLayout {
        width: 60;
        max-height: 80%;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = UserForm()
        yield self.form.build_layout()

    @on(Form.Submitted)
    def on_submitted(self, event: Form.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"Form submitted: {data}", severity="information")

    @on(Form.Cancelled)
    def on_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Form cancelled", severity="warning")
        self.exit()


if __name__ == "__main__":
    app = FormApp()
    app.run()
