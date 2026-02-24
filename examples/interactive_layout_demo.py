"""
Interactive demo showing field container layout options.

Use radio buttons to switch between different layout styles in real-time.

Run with: python examples/interactive_layout_demo.py
"""

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container, ScrollableContainer
from textual.widgets import Static, RadioButton, RadioSet
from textual_wtf import Form, StringField, IntegerField, Required, MinLength


class DemoForm(Form):
    """Demo form with configurable layout."""

    field_container_defaults = {
        'layout': 'vertical',
        'placeholder': False,
        'help_style': 'below',
    }

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


class InteractiveDemoApp(App):
    """Interactive app for exploring layout options."""

    CSS = """
    Screen {
        layout: vertical;
        overflow: hidden;
    }

    .demo-title {
        dock: top;
        height: 3;
        text-style: bold;
        text-align: center;
        background: $primary;
        color: $text;
        padding: 1;
    }

    .demo-scroll {
        height: 1fr;
        width: 100%;
    }

    .demo-content {
        width: 80;
        padding: 1 2;
    }

    .controls-section {
        background: $surface;
        padding: 1 2;
        margin-bottom: 1;
        border: solid $accent;
    }

    .control-group {
        height: auto;
        padding: 1 0;
    }

    .control-label {
        text-style: bold;
        padding-bottom: 1;
    }

    RadioSet {
        height: auto;
        layout: horizontal;
        border: none;
        background: transparent;
        padding: 0;
    }

    RadioButton {
        margin-right: 3;
    }

    .form-separator {
        height: 1;
        background: $primary;
        margin: 1 0;
    }

    .form-layout {
        width: auto;
        height: auto;
        border: solid $accent;
        padding: 1;
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
    """

    def compose(self) -> ComposeResult:
        """Create the interactive demo UI."""
        yield Static("Interactive Layout Options Demo", classes="demo-title")

        with ScrollableContainer(classes="demo-scroll"):
            with Vertical(classes="demo-content"):
                # Controls section
                with Vertical(classes="controls-section"):
                    # Label style controls
                    with Vertical(classes="control-group"):
                        yield Static("Label Style:", classes="control-label")
                        with RadioSet(id="label-style"):
                            yield RadioButton("Above", id="label-above")
                            yield RadioButton("Alongside", id="label-alongside")
                            yield RadioButton("Placeholder", id="label-placeholder", value=True)

                    # Help text controls
                    with Vertical(classes="control-group"):
                        yield Static("Help Text:", classes="control-label")
                        with RadioSet(id="help-style"):
                            yield RadioButton("Below", id="help-below", value=True)
                            yield RadioButton("Tooltip", id="help-tooltip")

                # Separator
                yield Static("", classes="form-separator")

                # Form container (will be replaced when options change)
                with Container(id="form-container"):
                    self.current_form = DemoForm()
                    yield self.current_form.render()

                # Add some padding at bottom for scrolling
                yield Static("")
                yield Static("")

    def on_mount(self) -> None:
        """Set up initial state."""
        # Set initial radio selections to match defaults
        self.query_one("#label-placeholder", RadioButton).value = True
        self.query_one("#help-below", RadioButton).value = True

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio button changes - rebuild form with new options."""
        # Determine current selections
        label_style_set = self.query_one("#label-style", RadioSet)
        help_style_set = self.query_one("#help-style", RadioSet)

        # Get selected radio button IDs
        label_pressed = label_style_set.pressed_button
        help_pressed = help_style_set.pressed_button

        if not label_pressed or not help_pressed:
            return  # Not fully initialized yet

        # Map radio button IDs to layout options
        label_id = label_pressed.id
        help_id = help_pressed.id

        # Determine layout and placeholder based on label style
        if label_id == "label-above":
            layout = "vertical"
            placeholder = False
        elif label_id == "label-alongside":
            layout = "horizontal"
            placeholder = False
        else:  # label-placeholder
            layout = "vertical"
            placeholder = True

        # Determine help style
        help_style = "below" if help_id == "help-below" else "tooltip"

        # Update form class defaults
        DemoForm.field_container_defaults = {
            'layout': layout,
            'placeholder': placeholder,
            'help_style': help_style,
        }

        # Rebuild form with new options
        self.rebuild_form()

    def rebuild_form(self) -> None:
        """Rebuild the form with current layout options."""
        # Get current form data before rebuilding
        old_data = self.current_form.get_data()

        # Remove old form
        form_container = self.query_one("#form-container")
        form_container.remove_children()

        # Create new form with preserved data and apply tooltips if needed
        self.current_form = DemoForm(data=old_data)
        layout = self.current_form.render()

        # If help_style is tooltip, add tooltips to field containers
        if self.current_form.field_container_defaults.get('help_style') == 'tooltip':
            for bound_field in self.current_form.bound_fields.values():
                if bound_field.field.help_text and hasattr(bound_field, "widghet") and bound_field.widget:
                    # Set tooltip on the widget
                    bound_field.widget.tooltip = bound_field.field.help_text

        form_container.mount(layout)

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


if __name__ == "__main__":
    app = InteractiveDemoApp()
    app.run()
