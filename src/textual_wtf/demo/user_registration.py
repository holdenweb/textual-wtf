"""User registration form example with results display"""
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static
from textual_wtf import Form, StringField, BooleanField
from textual_wtf.validators import EmailValidator
from textual_wtf.demo.results_screen import ResultsDisplayScreen

class RegistrationForm(Form):
    """User registration form"""
    username = StringField(
        label="Username",
        required=True,
        help_text="Choose a unique username"
    )
    email = StringField(
        label="Email Address",
        required=True,
        validators=[EmailValidator()]
    )
    full_name = StringField(
        label="Full Name",
        required=True
    )
    agree_terms = BooleanField(
        label="I agree to the terms and conditions",
    )


class ResultsScreen(ResultsDisplayScreen):
    """Utility Screen to display form results"""

    def compose(self) -> ComposeResult:
        with Container(id="results-container"):
            yield Static(self.result_title, id="results-title")

            yield from self.show_data()
            yield from self.buttons()


class RegistrationScreen(Screen):
    """User registration application"""

    TITLE = "User Registration"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS = """
    Container {
        align: center middle;
    }

    #info {
        width: 60;
        height: auto;
        margin: 1 0;
        padding: 1;
        border: solid blue;
    }

    RenderedForm {
        width: 60;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll():
                yield Static(
                    "Welcome! Please fill out the registration form below.",
                    id="info"
                )
                self.form = RegistrationForm(title="Create Account")
                yield self.form.render()

    def on_form_submitted(self, event: Form.Submitted):
        """Handle successful registration"""
        data = event.form.get_data()

        if not data['agree_terms']:
            self.notify(
                "You must agree to the terms and conditions",
                severity="error"
            )
            return

        def check_reset(cont):
            if cont:
                self.reset_form()
            else:
                self.dismiss(cont)

        self.app.push_screen(
            ResultsScreen("Registration Successful!", data), check_reset
        )

    def on_form_cancelled(self, event: Form.Cancelled):
        """Handle registration cancellation"""

        def check_reset(cont):
            if cont:
                self.reset_form()
            else:
                self.dismiss(cont)

        self.app.push_screen(ResultsScreen("Registration Cancelled", None), check_reset)

    def reset_form(self):
        """Clear form and create fresh one"""
        old_form = self.query_one("RenderedForm")
        old_form.remove()
        self.form = RegistrationForm(title="Create Account")
        self.query_one("VerticalScroll").mount(self.form.render())


class RegistrationApp(App):

    def on_mount(self):
        self.app.push_screen(RegistrationScreen(), callback=self.exit_app)

    def exit_app(self, result=None) -> None:
        """Called when Screen is dismissed."""
        self.exit(result)


def main():
    RegistrationApp().run()

if __name__ == "__main__":
    main()

