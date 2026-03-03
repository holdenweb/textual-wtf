"""Entry point for the textual-wtf demo suite.

Run with:
    python -m examples
"""

from textual.app import App

from .chooser_screen import ChooserScreen, DemoEntry
from .form_composition_demo import FormCompositionDemoScreen
from .interactive_layout_demo import InteractiveDemoScreen
from .password_change_demo import PasswordChangeDemoScreen
from .rendering_modes_demo import RenderingModesDemoScreen
from .tabbed_settings_demo import TabbedSettingsDemoScreen
from .validator_gallery_demo import ValidatorGalleryDemoScreen


DEMOS: list[DemoEntry] = [
    DemoEntry(
        title="Rendering Modes",
        description="form.layout() vs simple_layout() vs bf() + FieldErrors, side by side",
        screen_class=RenderingModesDemoScreen,
    ),
    DemoEntry(
        title="Form Composition",
        description="Embedded sub-forms; prefixed fields; copy-billing-to-shipping",
        screen_class=FormCompositionDemoScreen,
    ),
    DemoEntry(
        title="Validator Gallery",
        description="Required, MinLength, MaxLength, EmailValidator, FunctionValidator, custom Validator",
        screen_class=ValidatorGalleryDemoScreen,
    ),
    DemoEntry(
        title="Password Change",
        description="Cross-field validation via clean_form() and add_error()",
        screen_class=PasswordChangeDemoScreen,
    ),
    DemoEntry(
        title="Tabbed Settings",
        description="TabbedForm with set_data() pre-population and get_data() round-trip",
        screen_class=TabbedSettingsDemoScreen,
    ),
    DemoEntry(
        title="Interactive Layout",
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
