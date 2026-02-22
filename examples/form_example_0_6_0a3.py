"""
Example demonstrating version 0.6.0a3 - BoundField with protocols/mixins.

This combines:
- Declarative Form syntax (like 0.5.x)
- BoundField pattern (like 0.5.x)
- New protocols/mixins architecture (from your design)

Run with: python examples/form_example_0_6_0a3.py
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button
from textual_wtf import Form, StringField, IntegerField, Required, MinLength


class UserForm(Form):
    """Simple user form using declarative syntax."""

    name = StringField(
        label="Name",
        required=True,
        validators=[Required(), MinLength(3)],
        placeholder="Enter your name"
    )

    age = IntegerField(
        label="Age",
        required=False,
        min_value=0,
        max_value=130,
        placeholder="Enter your age"
    )


class FormApp(App):
    """App demonstrating the new Form/BoundField architecture."""

    CSS = """
    Screen {
        align: center middle;
    }

    #form-container {
        width: 60;
        border: solid $primary;
        padding: 1 2;
    }

    Button {
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the form."""
        with Container(id="form-container"):
            # Create form instance
            self.form = UserForm()

            # Render form fields (they're BoundField widgets now)
            for bound_field in self.form.bound_fields.values():
                yield bound_field

            yield Button("Submit", variant="primary", id="submit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle submit button."""
        if event.button.id == "submit":
            # Validate form
            if self.form.is_valid():
                data = self.form.get_data()
                self.notify(f"Form valid! Data: {data}", severity="information")
            else:
                errors = self.form.errors
                self.notify(f"Errors: {errors}", severity="error")


if __name__ == "__main__":
    app = FormApp()
    app.run()
