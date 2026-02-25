"""Entry point for the textual-wtf demo suite.

Run with:
    python -m examples
"""

from textual.app import App

from .chooser_screen import ChooserScreen, DemoEntry
from .form_example_0_6_0a3 import FormExampleScreen
from .interactive_layout_demo import InteractiveDemoScreen
from .layout_options_demo import LayoutOptionsDemoScreen
from .simple_field_example import SimpleFieldExampleScreen
from .simple_rendered_form import SimpleRenderedFormScreen


DEMOS: list[DemoEntry] = [
    DemoEntry(
        title="Simple Rendered Form",
        description="Form.build_layout() with Submitted/Cancelled handling",
        screen_class=SimpleRenderedFormScreen,
    ),
    DemoEntry(
        title="Simple Field Example",
        description="Direct BoundField usage without DefaultFormLayout",
        screen_class=SimpleFieldExampleScreen,
    ),
    DemoEntry(
        title="Layout Options Demo",
        description="Three layout styles (above / beside / placeholder) side-by-side",
        screen_class=LayoutOptionsDemoScreen,
    ),
    DemoEntry(
        title="Form Example 0.6.0a3",
        description="BoundField with protocols/mixins architecture",
        screen_class=FormExampleScreen,
    ),
    DemoEntry(
        title="Interactive Layout Demo",
        description="Switch label/help styles in real-time with radio buttons",
        screen_class=InteractiveDemoScreen,
    ),
]


class FormDemoApp(App[None]):
    """TUI demo app for textual-wtf form components."""

    CSS_PATH = "__main__.css"

    TITLE = "Forms Demonstrator"

    def on_mount(self) -> None:
        """Push the chooser screen on startup."""
        self.push_screen(ChooserScreen(DEMOS))


def main() -> None:
    app = FormDemoApp()
    app.run()


if __name__ == "__main__":
    main()
