"""Basic form example with results display"""
from textual.app import App, ComposeResult
from textual.containers import Container, Center
from textual.widgets import Static, Button
from textual_forms import Form, StringField, IntegerField, BooleanField
from results_screen import ResultsDisplayScreen  # Demo library utility

class UserForm(Form):
    """Simple user registration form"""
    name = StringField(label="Name", required=True)
    age = IntegerField(label="Age", min_value=0, max_value=130)
    active = BooleanField(label="Active User")


class ResultScreen(ResultsDisplayScreen):
    """Utility Screen to display form results"""

    def compose(self) -> ComposeResult:
        with Container(id="results-container"):
            yield Static(self.result_title, id="results-title")

            yield from self.show_data()
            yield from self.buttons()


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

        self.push_screen(ResultScreen("Form Submitted Successfully!", data), check_reset)

    def on_form_cancelled(self, event: Form.Cancelled):
        """Handle form cancellation"""
        # Show cancellation screen
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()

        self.push_screen(ResultScreen("Form Cancelled", None), check_reset)

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
