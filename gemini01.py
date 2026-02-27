from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log
from textual_wtf import Form, StringField, IntegerField, EmailValidator

# 1. Define a reusable sub-form
class AddressForm(Form):
    street = StringField("Street", help_text="Street address or P.O. Box")
    city = StringField("City")
    zip_code = IntegerField("Zip Code", help_text="5-digit zip")

# 2. Define the main form and embed the AddressForm
class UserProfileForm(Form):
    title = "User Profile"
    
    username = StringField("Username", min_length=3)
    email = StringField("Email", validators=[EmailValidator()])
    
    # Use the .embed() method to include the address fields
    # This will create fields like 'addr_street', 'addr_city', etc.
    address = AddressForm()

class FormApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    UserProfileForm {
        width: 50;
        border: panel $primary;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        # 3. Build the layout from the form instance
        yield UserProfileForm().build_layout() 
        yield Log(id="output")
        yield Footer()

    # 4. Handle the Submitted message
    def on_user_profile_form_submitted(self, event: UserProfileForm.Submitted) -> None:
        data = event.form.get_data()
        log = self.query_one("#output", Log)
        log.write_line(f"Form Submitted! Data: {data}")

if __name__ == "__main__":
    app = FormApp()
    app.run()
