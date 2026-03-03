"""ChooserScreen — lists available demos and lets the user pick one."""

from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static


@dataclass
class DemoEntry:
    """Metadata for a single demo program."""

    title: str
    description: str
    screen_class: type  # a Screen subclass


class ChooserScreen(Screen):
    """The demo-chooser screen.

    Shows a titled panel listing all available demos.  Press Enter (or click)
    on an item to push that demo's Screen; press Escape to quit.
    """

    BINDINGS = [Binding("escape", "quit", "Quit")]

    DEFAULT_CSS = """
    ChooserScreen {
        align: center middle;
    }

    #chooser-panel {
        width: 70;
        height: auto;
        max-height: 90%;
        border: double $primary;
        padding: 1 2;
    }

    #chooser-title {
        text-style: bold;
        text-align: center;
        background: $primary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
    }

    #chooser-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    ListView {
        height: auto;
        border: solid $accent;
    }

    ListItem {
        padding: 0 1;
        height: auto;
    }

    .item-title {
        text-style: bold;
    }

    .item-desc {
        color: $text-muted;
    }

    #chooser-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, demos: list[DemoEntry], **kwargs) -> None:
        super().__init__(**kwargs)
        self._demos = demos

    def compose(self) -> ComposeResult:
        with Vertical(id="chooser-panel"):
            yield Static("textual-wtf Form Demos", id="chooser-title")
            yield Static("Select a demo to run", id="chooser-subtitle")
            with ListView(id="demo-list"):
                for entry in self._demos:
                    with ListItem():
                        yield Static(entry.title, classes="item-title")
                        yield Static(entry.description, classes="item-desc")
            yield Static(
                "↑↓ navigate  •  Enter / click to open  •  Escape to quit",
                id="chooser-hint",
            )

    def action_quit(self) -> None:
        """Exit the application."""
        self.app.exit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Push the selected demo screen onto the stack."""
        index = event.list_view.index
        if index is not None and 0 <= index < len(self._demos):
            screen_class = self._demos[index].screen_class
            self.app.push_screen(screen_class())
