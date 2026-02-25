"""
Example demonstrating different FieldContainer layout options.

Run with: python -m examples  (select "Layout Options Demo")
"""

from textual.app import ComposeResult, on
from textual.containers import Vertical

from .example_screen import ExampleScreen
from textual.widgets import Static
from textual_wtf import Form, StringField, IntegerField


class VerticalForm(Form):
    """Default vertical layout with labels above fields."""
    label_style = "above"

    name = StringField(label="Name", required=True, min_length=3)
    age = IntegerField(label="Age", minimum=0, maximum=130)


class HorizontalForm(Form):
    """Horizontal layout with labels left of fields."""
    label_style = "beside"

    name = StringField(label="Name", required=True, min_length=3)
    age = IntegerField(label="Age", minimum=0, maximum=130)


class PlaceholderForm(Form):
    """Ultra-compact with placeholder labels."""
    label_style = "placeholder"

    name = StringField(label="Name", required=True, min_length=3)
    age = IntegerField(label="Age", minimum=0, maximum=130)


class LayoutOptionsDemoScreen(ExampleScreen):
    """Screen showing different layout options side-by-side."""

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
    }
    """

    def compose(self) -> ComposeResult:
        """Create three forms with different layouts."""

        # Vertical layout
        with Vertical(classes="demo-section"):
            yield Static("Vertical (Default)", classes="demo-title")
            yield Static("Labels above fields")
            form1 = VerticalForm()
            yield form1.build_layout()

        # Horizontal layout
        with Vertical(classes="demo-section"):
            yield Static("Horizontal", classes="demo-title")
            yield Static("Labels left of fields")
            form2 = HorizontalForm()
            yield form2.build_layout()

        # Placeholder layout
        with Vertical(classes="demo-section"):
            yield Static("Placeholder", classes="demo-title")
            yield Static("Labels as placeholders")
            form3 = PlaceholderForm()
            yield form3.build_layout()

    @on(Form.Submitted)
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
        self.action_back()
