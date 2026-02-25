"""Entry point for the textual-wtf demo suite.

Run with:
    python -m examples
"""

from textual.app import App

from .chooser_screen import ChooserScreen, DemoEntry
from .embedded_forms_demo import EmbeddedFormsDemoScreen
from .interactive_layout_demo import InteractiveDemoScreen
from .layout_options_demo import LayoutOptionsDemoScreen
from .simple_rendered_form import SimpleRenderedFormScreen


DEMOS: list[DemoEntry] = [
    DemoEntry(
        title="Simple Rendered Form",
        description="Form.build_layout() with Submitted/Cancelled handling",
        screen_class=SimpleRenderedFormScreen,
    ),
    DemoEntry(
        title="Layout Options Demo",
        description="Three layout styles (above / beside / placeholder) side-by-side",
        screen_class=LayoutOptionsDemoScreen,
    ),
    DemoEntry(
        title="Embedded Forms",
        description="Two forms side by side; inspect any field by name",
        screen_class=EmbeddedFormsDemoScreen,
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
