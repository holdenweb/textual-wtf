"""
Simple example demonstrating the new Field architecture (v6.0.0a2).

Run with: python examples/simple_field_example.py
"""

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Button
from textual_wtf import Field, FormInput, Required, MinLength


class SimpleFormApp(App):
    """Simple app demonstrating the new Field API."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
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
        with Container(id="form-container"):
            # Create name field with FormInput widget
            yield Field(
                name="name",
                widget=FormInput,
                label="Name",
                validators=[Required(), MinLength(3)],
                validate_on=("blur",),
                required=True,
                placeholder="Enter your name"
            )
            
            # Create email field
            yield Field(
                name="email",
                widget=FormInput,
                label="Email",
                validators=[Required()],
                validate_on=("blur",),
                required=True,
                type="email",
                placeholder="Enter your email"
            )
            
            # Submit button
            yield Button("Submit", variant="primary", id="submit")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle submit button."""
        if event.button.id == "submit":
            # Validate all fields
            name_field = self.query_one(Field)
            if name_field.validate():
                self.notify(f"Form valid! Name: {name_field.value}", severity="information")
            else:
                self.notify("Please fix errors", severity="error")


if __name__ == "__main__":
    app = SimpleFormApp()
    app.run()
