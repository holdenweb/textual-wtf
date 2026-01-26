"""Basic form example with results display"""
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button
from textual_forms import Form, StringField, IntegerField, BooleanField


class UserForm(Form):
    """Simple user registration form"""
    name = StringField(label="Name", required=True)
    age = IntegerField(label="Age", min_value=0, max_value=130)
    active = BooleanField(label="Active User")


class ResultsScreen(Screen):
    """Screen to display form results"""

    CSS = """
    ResultsScreen {
        align: center middle;
    }

    #results-container {
        width: 60;
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

    #buttons {
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, data: dict = None):
        super().__init__()
        self.result_title = title
        self.data = data

    def compose(self) -> ComposeResult:
        with Container(id="results-container"):
            yield Static(self.result_title, id="results-title")

            if self.data:
                # Format data nicely
                lines = []
                for key, value in self.data.items():
                    lines.append(f"{key}: {value}")
                yield Static("\n".join(lines), id="results-data")
            else:
                yield Static("Form was cancelled", id="results-data")

            with Center(id="buttons"):
                yield Button("New Form", variant="primary", id="new")
                yield Button("Exit", id="exit")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "new":
            # Pop results screen and reset form
            self.dismiss(True)
        elif event.button.id == "exit":
            self.app.exit()


class BasicFormApp(App):
    """Demo app for basic form"""

    CSS_PATH = "basic_form.tcss"

    def compose(self) -> ComposeResult:
        self.form = UserForm(title="User Registration")
        yield self.form.render()

    def on_form_submitted(self, event: Form.Submitted):
        """Handle form submission"""
        data = event.form.get_data()
        # Show results screen
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()

        self.push_screen(ResultsScreen("Form Submitted Successfully!", data), check_reset)

    def on_form_cancelled(self, event: Form.Cancelled):
        """Handle form cancellation"""
        # Show cancellation screen
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()

        self.push_screen(ResultsScreen("Form Cancelled", None), check_reset)

    def reset_form(self):
        """Clear form and create fresh one"""
        # Remove old form
        old_form = self.query_one("RenderedForm")
        old_form.remove()

        # Create and mount new form
        self.form = UserForm(title="User Registration")
        self.mount(self.form.render())

    def on_click(self):
        self.app.log(self.css_tree)
        self.app.log(self.tree)


if __name__ == "__main__":
    BasicFormApp().run()
