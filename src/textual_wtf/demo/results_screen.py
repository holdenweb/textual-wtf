from textual.app import ComposeResult, on
from textual.containers import Center
from textual.screen import Screen
from textual.widgets import Button, Static

class ResultsDisplayScreen(Screen):
    """
    Screen to display form results.

    Subclasses must add a compose() method to implement the visual rendering.
    """

    CSS = """
    ResultsScreen {
        align: center middle;
    }

    #results-container {
        width: 80%;
        height: auto;
        border: heavy green;
        padding: 1;
    }

    #results-title {
        background: green;
        color: white;
        width: 100%;
        height: 1;
        content-align: center middle;
        margin-bottom: 1;
    }

    #results-data {
        background: $panel;
        padding: 1;
        margin: 1 0;
    }

    #field-lookup {
        background: $panel;
        padding: 1;
        margin: 1 0;
        border: solid blue;
    }

    #buttons {
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, data: dict = None, form=None):
        super().__init__()
        self.result_title = title
        self.data = data
        self.form = form

    def compose(self) -> ComposeResult:
        raise NotImplementedError("ResultsScreen subclasses must define a compose() method")

    @on(Button.Pressed, "#new")
    def new_pressed(self, event: Button.Pressed):
        self.dismiss(True)

    @on(Button.Pressed, "#exit")
    def exit_pressed(self, event: Button.Pressed):
            self.dismiss(False)

    def show_data(self):

        if self.data:
            # Format data nicely
            lines = []
            for key, value in self.data.items():
                lines.append(f"{key}: {value}")
            yield Static("\n".join(lines), id="results-data")

    def buttons(self) -> ComposeResult:
        with Center(id="buttons"):
            yield Button("New Form", variant="primary", id="new")
            yield Button("Exit", id="exit")


