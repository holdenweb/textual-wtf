from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static


class ChooserScreen( Screen ):
    """The main application screen."""

    BINDINGS = [
        Binding( "escape", "quit", "Close" )
    ]

    def compose(self):
        with Vertical():
            yield Static("The simplest possible window?")

    def on_click(self, event):
        self.app.push_screen("app_screen")
