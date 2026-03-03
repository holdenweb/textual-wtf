"""
Interactive demo showing label and help-text style options.

A single form is displayed on the left.  Two radio sets on the right let
you switch the label style (above / beside / placeholder) and the help-text
style (below / tooltip) independently.  The form rebuilds instantly on each
change, preserving any data already entered.

Run with: python -m examples  (select "Interactive Layout Demo")
"""

from textual.app import ComposeResult, on
from textual.containers import Horizontal, Vertical
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
        help_text="Enter your full name",
    )
    age = IntegerField(
        label="Age",
        minimum=20,
        maximum=130,
        help_text="Enter your age in years",
    )


class InteractiveDemoScreen(ExampleScreen):
    """Single form whose label and help-text styles are controlled by radio sets."""

    CSS_PATH = """ids.css"""

    def compose(self) -> ComposeResult:
        self._label_style = "above"
        self._help_style = "below"
        self._form = DemoForm(label_style=self._label_style, help_style=self._help_style)

        with Vertical(id="form-col"):
            yield self._form.layout()

        with Vertical(id="controls-col"):
            yield Static("Label Style", classes="control-label")
            with RadioSet(id="label-style"):
                yield RadioButton("Above", id="label-above", value=True)
                yield RadioButton("Alongside", id="label-beside")
                yield RadioButton("Placeholder", id="label-placeholder")

            yield Static("Help Text Style", classes="control-label")
            with RadioSet(id="help-style"):
                yield RadioButton("Below", id="help-below", value=True)
                yield RadioButton("Tooltip", id="help-tooltip")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Rebuild the form when either style control changes."""
        if event.radio_set.id == "label-style" and event.pressed:
            self._label_style = event.pressed.id.removeprefix("label-")
        elif event.radio_set.id == "help-style" and event.pressed:
            self._help_style = event.pressed.id.removeprefix("help-")
        else:
            return
        self._rebuild_form()

    def _rebuild_form(self) -> None:
        """Replace the form widget, preserving current field values."""
        old_data = self._form.get_data()
        self._form = DemoForm(
            data=old_data,
            label_style=self._label_style,
            help_style=self._help_style,
        )
        form_col = self.query_one("#form-col")
        form_col.remove_children()
        form_col.mount(self._form.layout())

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        data = event.form.get_data()
        self.notify(f"Submitted: {data}", severity="information")

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Cancelled", severity="warning")
        self.action_back()


if __name__ == "__main__":
    print("Run the full demo suite with:  python -m examples")
