"""
Example demonstrating different FieldContainer layout options.

Run with: python examples/layout_options_demo.py
"""

from textual.app import App, ComposeResult, on
from textual.containers import Vertical
from textual.widgets import Static
from textual_wtf import Form, StringField, IntegerField, Required, MinLength


class VerticalForm(Form):
    """Default vertical layout with labels above fields."""
    field_container_defaults = {
        'layout': 'vertical',
        'placeholder': False,
        'help_style': 'below',
    }

    name = StringField(label="Name", validators=[Required(), MinLength(3)])
    age = IntegerField(label="Age", min_value=0, max_value=130)


class HorizontalForm(Form):
    """Horizontal layout with labels left of fields."""
    field_container_defaults = {
        'layout': 'horizontal',
        'placeholder': False,
        'help_style': 'below',
    }

    name = StringField(label="Name", validators=[Required(), MinLength(3)])
    age = IntegerField(label="Age", min_value=0, max_value=130)


class PlaceholderForm(Form):
    """Ultra-compact with placeholder labels."""
    field_container_defaults = {
        'layout': 'vertical',
        'placeholder': True,
        'help_style': 'below',
    }

    name = StringField(label="Name", validators=[Required(), MinLength(3)])
    age = IntegerField(label="Age", min_value=0, max_value=130)


class LayoutDemoApp(App):
    """App showing different layout options side-by-side."""

    CSS = """
    Screen {
        layout: horizontal;
        overflow: auto;
    }

    .demo-section {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 1 2;
        margin: 0 1;
    }

    .demo-title {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }

    .form-layout {
        width: auto;
        height: auto;
        border: solid $accent;
        padding: 1;
        margin-top: 1;
    }

    .field-container {
        height: auto;
        margin-bottom: 1;
    }

    .field-label {
        text-style: bold;
        width: 10;
    }

    .field-horizontal {
        layout: horizontal;
        height: auto;
    }

    .field-horizontal .field-label {
        width: 10;
        padding-right: 1;
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
    Input {
        &.-invalid {
            border-left: thick red;
            border-right: thick red;
        }
        &.-valid {
            border-left: blank red;
            border-right: blank red;
        }

    """

    def compose(self) -> ComposeResult:
        """Create three forms with different layouts."""

        # Vertical layout
        with Vertical(classes="demo-section"):
            yield Static("Vertical (Default)", classes="demo-title")
            yield Static("Labels above fields")
            form1 = VerticalForm()
            yield form1.render()

        # Horizontal layout
        with Vertical(classes="demo-section"):
            yield Static("Horizontal", classes="demo-title")
            yield Static("Labels left of fields")
            form2 = HorizontalForm()
            yield form2.render()

        # Placeholder layout
        with Vertical(classes="demo-section"):
            yield Static("Placeholder", classes="demo-title")
            yield Static("Labels as placeholders")
            form3 = PlaceholderForm()
            yield form3.render()

    @on(From.Submitted)
    def on_submitted(self, event: Form.Submitted) -> None:
        """Handle form submission."""
        if event.form.is_valid():
            data = event.form.get_data()
            self.notify(f"Form submitted: {data}", severity="information")
        else:
            self.notify("Please fix errors", severity="error")

    @on(Form.Cancelled)
    def on_cancelled(self, event: Form.Cancelled) -> None:
        """Handle form cancellation."""
        self.notify("Form cancelled", severity="warning")


if __name__ == "__main__":
    app = LayoutDemoApp()
    app.run()
