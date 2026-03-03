"""Shared base Screen class for textual-wtf examples."""

import inspect
from pathlib import Path

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static


class ExampleScreen(Screen):
    """Base Screen for textual-wtf example programs.

    Provides:
    - A one-row inverted header (docked top) showing the example's source path.
    - An empty one-row footer (docked bottom), reserved for future use.
    - Default centred layout for screen content (overridable per example).
    - Escape key returns to the previous screen (or quits if this is the root).
    """

    BINDINGS = [Binding("escape", "back", "Back")]

    DEFAULT_CSS = """
    Screen {
        align: center middle;
    }
    .example-header {
        dock: top;
        height: 1;
        background: $foreground;
        color: $background;
        padding: 0 1;
    }
    .example-footer {
        dock: bottom;
        height: 1;
        background: $panel;
    }
    """

    def action_back(self) -> None:
        """Return to the previous screen, or quit if this is the root screen."""
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()

    def on_mount(self) -> None:
        """Add the header and footer chrome to the screen."""
        try:
            source_file = inspect.getfile(type(self))
            source_path = str(Path(source_file).relative_to(Path.cwd()))
        except (TypeError, OSError, ValueError):
            try:
                source_path = inspect.getfile(type(self))
            except (TypeError, OSError):
                source_path = "<unknown>"

        self.mount(Static(source_path, classes="example-header"), before=0)
        self.mount(Static("", classes="example-footer"))
