"""
Interactive demo showing field container layout options.

All three label styles are displayed side by side so you can compare them
at a glance.  A single control switches the help-text style across all
three columns simultaneously.

Run with: python -m examples  (select "Interactive Layout Demo")
"""

from textual.app import ComposeResult, on
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from .example_screen import ExampleScreen
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


# (container-id, label_style value, column heading)
_COLUMNS = [
    ("col-above",       "above",       "Above"),
    ("col-beside",      "beside",      "Alongside"),
    ("col-placeholder", "placeholder", "Placeholder"),
]


class InteractiveDemoScreen(ExampleScreen):
    """Interactive app for exploring all three label-style options at once."""

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
        padding: 1 2;
    }

    .controls-section {
        height: auto;
        background: $surface;
        padding: 0 2;
        margin-bottom: 1;
        border: solid $accent;
    }

    .control-group {
        height: auto;
        padding: 0;
    }

    .control-label {
        text-style: bold;
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

    #forms-row {
        height: auto;
        layout: horizontal;
    }

    .form-col {
        width: 1fr;
        height: auto;
        border: solid $primary;
        margin: 0 1;
        padding: 0;
    }

    .col-title {
        text-style: bold;
        background: $primary;
        color: $text;
        text-align: center;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the interactive demo UI."""
        yield Static("Interactive Layout Options Demo", classes="demo-title")

        with ScrollableContainer(classes="demo-scroll"):
            with Vertical(classes="demo-content"):
                # Single control: help-text style (label style shown as column headers)
                with Vertical(classes="controls-section"):
                    with Vertical(classes="control-group"):
                        yield Static("Help Text Style:", classes="control-label")
                        with RadioSet(id="help-style"):
                            yield RadioButton("Below", id="help-below", value=True)
                            yield RadioButton("Tooltip", id="help-tooltip")

                # Three forms side by side, one per label style
                with Horizontal(id="forms-row"):
                    for col_id, label_style, title in _COLUMNS:
                        with Vertical(classes="form-col"):
                            yield Static(title, classes="col-title")
                            with Container(id=col_id):
                                form = DemoForm(label_style=label_style)
                                setattr(self, f"_form_{label_style}", form)
                                yield form.build_layout()

    def on_mount(self) -> None:
        """Set up initial state."""
        super().on_mount()
        self._help_style = "below"

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Rebuild all three forms when the help-text style changes."""
        help_pressed = self.query_one("#help-style", RadioSet).pressed_button
        if not help_pressed:
            return
        self._help_style = "below" if help_pressed.id == "help-below" else "tooltip"
        self._rebuild_all()

    def _rebuild_all(self) -> None:
        """Rebuild all three form columns with the current help style."""
        for col_id, label_style, _title in _COLUMNS:
            old_form: DemoForm = getattr(self, f"_form_{label_style}")
            old_data = old_form.get_data()
            col = self.query_one(f"#{col_id}")
            col.remove_children()
            new_form = DemoForm(
                data=old_data,
                label_style=label_style,
                help_style=self._help_style,
            )
            setattr(self, f"_form_{label_style}", new_form)
            col.mount(new_form.build_layout())

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
        self.action_back()


if __name__ == "__main__":
    print("Run the full demo suite with:  python -m examples")
