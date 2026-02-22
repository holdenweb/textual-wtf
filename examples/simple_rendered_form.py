"""
Simple example demonstrating form rendering.

Run with: python examples/simple_rendered_form.py
"""

from textual.app import App, ComposeResult
from textual_wtf import Form, StringField, IntegerField, Required, MinLength


class UserForm(Form):
    """Simple user registration form."""
    name = StringField(
        label="Name",
        validators=[Required(), MinLength(3)],
        help_text="Enter your full name"
    )
    age = IntegerField(
        label="Age",
        min_value=0,
        max_value=130,
        help_text="Enter your age in years"
    )


class FormApp(App):
    """Simple app that displays a form."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .form-layout {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }
    
    .field-container {
        height: auto;
    }
    
    .field-label {
        text-style: bold;
    }
    
    .field-help-text {
        color: $text-muted;
        text-style: italic;
    }
    
    .field-errors {
        color: $error;
        display: none;
    }
    
    .field-errors.visible {
        display: block;
    }
    
    .form-buttons {
        margin-top: 1;
        height: auto;
        layout: horizontal;
    }
    
    .form-buttons Button {
        margin-right: 2;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create and mount the form."""
        self.form = UserForm()
        yield self.form.render()
    
    def on_form_submitted(self, event: Form.Submitted) -> None:
        """Handle form submission."""
        if event.form.is_valid():
            data = event.form.get_data()
            self.notify(f"Form submitted: {data}", severity="information")
        else:
            self.notify("Please fix errors before submitting", severity="error")
    
    def on_form_cancelled(self, event: Form.Cancelled) -> None:
        """Handle form cancellation."""
        self.notify("Form cancelled", severity="warning")
        self.exit()


if __name__ == "__main__":
    app = FormApp()
    app.run()
