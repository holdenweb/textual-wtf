from textual.app import App
from .interactive_layout_demo import InteractiveDemoScreen
from .chooser_screen import ChooserScreen

class FormDemoApp( App[ None ] ):
    """TUI app for showing information about the Second Life grid."""

    CSS_PATH = "__main__.css"
    """The name of the CSS file for the app."""

    TITLE = "Forms Demonstrator"
    """str: The title of the application."""

    SCREENS = {
        "app_chooser": ChooserScreen,
        "app_screen": InteractiveDemoScreen,
    }
    """The collection of application screens."""

    def on_mount( self ) -> None:
        """Set up the application on startup."""
        self.push_screen( "app_chooser" )

def main():
    app = FormDemoApp()
    app.run()

if __name__ == '__main__':
    main()
