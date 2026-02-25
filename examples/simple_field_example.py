"""
Simple example demonstrating direct BoundField usage without DefaultFormLayout.

Demonstrates:
- Declaring a Form with StringField
- Yielding BoundField widgets directly into a custom container
- Manual submit button with form validation

This is a lower-level usage pattern; for the simplest approach see
simple_rendered_form.py which uses Form.build_layout().

Run with: python -m examples  (select "Simple Field Example")
"""

from textual.app import ComposeResult
from textual.containers import Container

from .example_screen import ExampleScreen
from textual.widgets import Button
from textual_wtf import Form, StringField


class SimpleForm(Form):
    """A simple form with two string fields."""

    name = StringField(
        label="Name",
        required=True,
        min_length=3,
        help_text="Enter your full name",
    )
    email = StringField(
        label="Email",
        required=True,
        help_text="Enter your email address",
    )


class SimpleFieldExampleScreen(ExampleScreen):
    """Screen demonstrating direct BoundField widget usage."""

    CSS = """
    #form-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    Button {
        margin: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the form fields."""
        self.form = SimpleForm()
        with Container(id="form-container"):
            # Yield BoundField widgets directly — no DefaultFormLayout
            for bound_field in self.form.bound_fields.values():
                yield bound_field
            yield Button("Submit", variant="primary", id="submit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle submit button."""
        if event.button.id == "submit":
            if self.form.is_valid():
                data = self.form.get_data()
                self.notify(f"Form valid! Data: {data}", severity="information")
            else:
                self.notify("Please fix the errors above", severity="error")
