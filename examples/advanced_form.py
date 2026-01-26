"""Advanced form example with results display"""
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container, Center
from textual.widgets import Static, Button
from textual_forms import (
    Form, StringField, IntegerField, BooleanField, ChoiceField, TextField
)
from textual_forms.validators import EmailValidator, EvenInteger


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


class ResultsScreen(Screen):
    """Screen to display form results"""
    
    CSS = """
    ResultsScreen {
        align: center middle;
    }
    
    #results-container {
        width: 70;
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
            self.dismiss(True)
        elif event.button.id == "exit":
            self.app.exit()


class AdvancedFormApp(App):
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
        
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()
        
        self.push_screen(ResultsScreen("Form Submitted Successfully!", data), check_reset)
    
    def on_form_cancelled(self, event: Form.Cancelled):
        """Handle form cancellation"""
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()
        
        self.push_screen(ResultsScreen("Form Cancelled", None), check_reset)
    
    def reset_form(self):
        """Clear form and create fresh one"""
        old_form = self.query_one("RenderedForm")
        old_form.remove()
        
        self.form = ContactForm(title="Contact Information")
        self.mount(self.form.render())


if __name__ == "__main__":
    AdvancedFormApp().run()
