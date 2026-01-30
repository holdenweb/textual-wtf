import sys
import os
import subprocess
import importlib.resources as i_r

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Label, Header, Footer
from textual.message import Message

from textual_wtf.demo.basic_form import BasicFormScreen as BasicScreen
from textual_wtf.demo.advanced_form import AdvancedFormScreen as AdvancedScreen
from textual_wtf.demo.user_registration import RegistrationScreen
from textual_wtf.demo.nested_once_form import ShopScreen as NestedOnceScreen
from textual_wtf.demo.nested_twice_form import ShopScreen as NestedTwiceScreen

class MenuLink(Label):
    """A clickable text link widget."""

    DEFAULT_CSS = """
    MenuLink {
        color: $accent;
        text-style: underline;
        margin-bottom: 1;
        width: auto;
        content-align: center middle;
    }
    MenuLink:hover {
        color: $text;
        text-style: bold underline;
        background: $accent 10%;
    }
    """

    class Clicked(Message):
        """Message posted when the link is clicked."""

        def __init__(self, link: "MenuLink") -> None:
            self.link = link
            super().__init__()



    def __init__(self, title: str, app_screen: Screen = None, is_exit: bool = False):
        super().__init__(title)
        self.app_screen = app_screen
        self.is_exit = is_exit

    def on_click(self) -> None:
        """Handle click event."""
        self.post_message(self.Clicked(self))


class LauncherApp(App):
    """A simple launcher for Textual Forms examples."""

    CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }

    #menu-container {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $panel;
        padding: 1 2;
    }

    #title-label {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        padding-bottom: 2;
        color: $text-muted;
    }

    /* Style the exit link differently */
    .exit-link {
        color: $error;
        margin-top: 1;
    }
    .exit-link:hover {
        color: $error-lighten-1;
        background: $error 10%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="menu-container"):
            yield Label("Select an Application", id="title-label")

            # Application Links
            yield MenuLink("1. Basic Form", app_screen=BasicScreen)
            yield MenuLink("2. Advanced Form", app_screen=AdvancedScreen)
            yield MenuLink("3. User Registration", app_screen=RegistrationScreen)
            yield MenuLink("4. Composition Example", app_screen=NestedOnceScreen)
            yield MenuLink("5. Multiply Included Example", app_screen=NestedTwiceScreen)

            # Exit Link
            yield MenuLink("Exit Launcher", is_exit=True)

        yield Footer()

    def on_menu_link_clicked(self, event: MenuLink.Clicked) -> None:
        """Handle the custom link click message."""
        link = event.link

        if link.is_exit:
            self.exit()
        elif link.app_screen:
            self.app.push_screen(link.app_screen())


def main():
        LauncherApp().run()


if __name__ == "__main__":
    main()