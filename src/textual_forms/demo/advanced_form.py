"""Advanced form example with results display"""
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static
from textual_forms import (
    Form, StringField, IntegerField, BooleanField, ChoiceField, TextField
)
from textual_forms.validators import EmailValidator, EvenInteger
from textual_forms.demo.results_screen import ResultsDisplayScreen

class ContactForm(Form):
    """Contact form with multiple field types"""
    name = StringField(
        label="Full Name",
        required=True,
        help_text="Enter your full name"
    )
    email = StringField(
        label="Email",
        required=True,
        validators=[EmailValidator()]
    )
    age = IntegerField(
        label="Age (even numbers only)",
        min_value=18,
        max_value=100,
        validators=[EvenInteger()]
    )
    country = ChoiceField(
        label="Country",
        choices=[
            ("us", "United States"),
            ("uk", "United Kingdom"),
            ("ca", "Canada"),
            ("au", "Australia"),
        ],
        required=True
    )
    subscribe = BooleanField(
        label="Subscribe to newsletter"
    )
    message = TextField(
        label="Message",
        help_text="Tell us about yourself"
    )


class ResultsScreen(ResultsDisplayScreen):
    """Utility Screen to display form results"""

    def compose(self) -> ComposeResult:
        with Container(id="results-container"):
            yield Static(self.result_title, id="results-title")

            yield from self.show_data()
            yield from self.buttons()


class AdvancedFormScreen(Screen):
    """Demo app for advanced form features"""

    CSS = """
    Screen {
        align: center middle;
    }

    RenderedForm {
        width: 60;
        height: auto;
        max-height: 90%;
    }
    """

    def compose(self) -> ComposeResult:
        # Pre-populate with example data
        initial_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "country": "us",
            "subscribe": True,
        }
        self.form = ContactForm(
            title="Contact Information",
            data=initial_data
        )
        yield self.form.render()

    def on_form_submitted(self, event: Form.Submitted):
        """Handle form submission"""
        data = event.form.get_data()

        def check_reset(cont):
            if cont:
                self.reset_form()
            else:
                self.dismiss(cont)

        self.app.push_screen(
            ResultsScreen("Form Submitted Successfully!", data), check_reset
        )

    def on_form_cancelled(self, event: Form.Cancelled):
        """Handle form cancellation"""

        def check_reset(cont):
            if cont:
                self.reset_form()
            else:
                self.dismiss(cont)

        self.app.push_screen(ResultsScreen("Form Cancelled", None), check_reset)

    def reset_form(self):
        """Clear form and create fresh one"""
        old_form = self.query_one("RenderedForm")
        old_form.remove()

        self.form = ContactForm(title="Contact Information")
        self.mount(self.form.render())

class AdvancedFormApp(App):

    def on_mount(self):
        self.app.push_screen(AdvancedFormScreen(), callback=self.exit_app)

    def exit_app(self, result=None) -> None:
        """Called when BasicFormScreen is dismissed."""
        self.exit(result)



def main():
    AdvancedFormApp().run()


if __name__ == "__main__":
    main()