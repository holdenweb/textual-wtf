"""
Interactive demo showing field container layout options.

Use radio buttons to switch between different layout styles in real-time.

Run with: python examples/interactive_layout_demo.py
"""

from textual.app import ComposeResult, on
from textual.containers import Vertical, Container, ScrollableContainer
from example_app import ExampleApp
from textual.widgets import Static, RadioButton, RadioSet
from textual_wtf import Form, StringField, IntegerField


class DemoForm(Form):
    """Demo form with configurable layout."""

    name = StringField(
        label="Name",
        required=True,
        min_length=3,
        max_length=12,
        help_text="Enter your full name"
    )
    age = IntegerField(
        label="Age",
        minimum=20,
        maximum=130,
        help_text="Enter your age in years"
    )


class InteractiveDemoApp(ExampleApp):
    """Interactive app for exploring layout options."""

    CSS = """
    Screen {
        layout: vertical;
        overflow: hidden;
        align: center middle;
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
        width: 80%;
    }

    .demo-content {
        width: 80;
        padding: 1 2;
    }

    .controls-section {
        height: auto;
        background: $surface;
        padding: 1 2;
        margin-bottom: 1;
        border: solid $accent;
        height: auto;
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
                    self.current_form = DemoForm(label_style="above")
                    yield self.current_form.build_layout()

                # Add some padding at bottom for scrolling
                yield Static("")
                yield Static("")

    def on_mount(self) -> None:
        """Set up initial state."""
        super().on_mount()
        self._label_style = "placeholder"
        self._help_style = "below"
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

        # Map radio button IDs to label_style values
        label_id = label_pressed.id
        help_id = help_pressed.id

        if label_id == "label-above":
            self._label_style = "above"
        elif label_id == "label-alongside":
            self._label_style = "beside"
        else:  # label-placeholder
            self._label_style = "placeholder"

        self._help_style = "below" if help_id == "help-below" else "tooltip"

        # Rebuild form with new options
        self.rebuild_form()

    def rebuild_form(self) -> None:
        """Rebuild the form with current layout options."""
        # Get current form data before rebuilding
        old_data = self.current_form.get_data()

        # Remove old form
        form_container = self.query_one("#form-container")
        form_container.remove_children()

        # help_style is a class-level attribute; set it before constructing
        DemoForm.help_style = self._help_style
        self.current_form = DemoForm(data=old_data, label_style=self._label_style)
        form_container.mount(self.current_form.build_layout())

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        """Handle form submission."""
        if event.form.is_valid():
            data = event.form.get_data()
            self.notify(f"Form submitted: {data}", severity="information")
        else:
            self.notify("Please fix errors before submitting", severity="error")

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        """Handle form cancellation."""
        self.notify("Form cancelled", severity="warning")


if __name__ == "__main__":
    app = InteractiveDemoApp()
    app.run()
