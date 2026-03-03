"""ChooserScreen — lists available demos and lets the user pick one."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static


HOVER_DEFAULT = (
    "Hover over a demo program to find out what it does.  Click to run it."
)


@dataclass
class DemoEntry:
    """Metadata for a single demo program."""

    title: str
    description: str
    screen_class: type  # a Screen subclass


class DemoListItem(ListItem):
    """Single-line list item that announces mouse-enter and mouse-leave."""

    class Hovered(Message):
        """Posted when the mouse enters this item."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class Left(Message):
        """Posted when the mouse leaves this item."""

    def __init__(self, index: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._index = index

    def on_enter(self) -> None:
        self.post_message(self.Hovered(self._index))

    def on_leave(self) -> None:
        self.post_message(self.Left())


class ChooserScreen(Screen):
    """The demo-chooser screen.

    Shows a titled panel with a scrollable list of demo names.  Hovering
    over an item (or navigating with ↑↓) reveals its description in the
    panel below the list.  Press Enter or click to run a demo; Escape quits.
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

    ListView {
        height: auto;
        max-height: 12;
        border: solid $accent;
    }

    DemoListItem {
        height: 1;
        padding: 0 1;
    }

    #demo-description {
        height: 4;
        margin-top: 1;
        border: solid $panel;
        padding: 0 1;
        color: $text-muted;
        background: $surface;
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
        with VerticalScroll(id="chooser-panel"):
            yield Static("textual-wtf Form Demos", id="chooser-title")
            with ListView(id="demo-list"):
                for i, entry in enumerate(self._demos):
                    with DemoListItem(i):
                        yield Static(entry.title)
            yield Static(HOVER_DEFAULT, id="demo-description")
            yield Static(
                "↑↓ navigate  •  Enter / click to open  •  Escape to quit",
                id="chooser-hint",
            )

    def _show_description(self, index: int | None) -> None:
        """Update the description panel; pass None to restore the default prompt."""
        text = (
            self._demos[index].description
            if index is not None
            else HOVER_DEFAULT
        )
        self.query_one("#demo-description", Static).update(text)

    def action_quit(self) -> None:
        """Exit the application."""
        self.app.exit()

    def on_demo_list_item_hovered(self, event: DemoListItem.Hovered) -> None:
        """Show the description for whichever item the mouse is over."""
        self._show_description(event.index)

    def on_demo_list_item_left(self, event: DemoListItem.Left) -> None:
        """Revert to the default prompt when the mouse leaves a list item."""
        self._show_description(None)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Show the description for the keyboard-highlighted item."""
        self._show_description(event.list_view.index)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Push the selected demo screen onto the stack."""
        index = event.list_view.index
        if index is not None and 0 <= index < len(self._demos):
            screen_class = self._demos[index].screen_class
            self.app.push_screen(screen_class())
