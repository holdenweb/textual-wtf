"""Form Composition Example with results display"""
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container, Center
from textual.widgets import Static, Button
from textual_forms import Form, StringField, BooleanField


# Define reusable forms
class AddressForm(Form):
    """Reusable address form"""
    street = StringField(label="Street Address", required=True)
    city = StringField(label="City", required=True)
    state = StringField(label="State/Province", required=True)
    postal_code = StringField(label="Postal Code", required=True)


class PersonalInfoForm(Form):
    """Personal information form"""
    first_name = StringField(label="First Name", required=True)
    last_name = StringField(label="Last Name", required=True)
    email = StringField(label="Email", required=True)
    phone = StringField(label="Phone")


# Compose forms together
class OrderForm(Form):
    """Order form composed from reusable forms"""
    
    # Personal information (no prefix - fields added directly)
    personal = PersonalInfoForm.compose()
    
    # Billing address (prefixed)
    billing = AddressForm.compose(prefix='billing')
    
    # Shipping address (prefixed)
    shipping = AddressForm.compose(prefix='shipping')
    
    # Additional fields
    same_as_billing = BooleanField(label="Shipping same as billing")
    notes = StringField(label="Order Notes")


class ResultsScreen(Screen):
    """Screen to display form results with SQL-style field lookup demo"""
    
    CSS = """
    ResultsScreen {
        align: center middle;
    }
    
    #results-container {
        width: 80;
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
        with Container(id="results-container"):
            yield Static(self.result_title, id="results-title")
            
            if self.data:
                # Format data nicely
                lines = []
                for key, value in self.data.items():
                    lines.append(f"{key}: {value}")
                yield Static("\n".join(lines), id="results-data")
                
                # Demonstrate SQL-style field lookup
                if self.form:
                    lookup_lines = [
                        "SQL-Style Field Lookup Examples:",
                        "  get_field('billing_street'): " + self.form.get_field('billing_street').label,
                        "  get_field('email'): " + self.form.get_field('email').label + " (unqualified)",
                        "",
                        "Note: get_field('street') would raise AmbiguousFieldError",
                        "      because both billing_street and shipping_street exist"
                    ]
                    yield Static("\n".join(lookup_lines), id="field-lookup")
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


class ShopApp(App):
    """Example application using composed forms"""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    RenderedForm {
        width: 80;
        height: 100%;
        max-height: 100%;
        border: heavy $accent;
    }
    """
    
    def compose(self):
        """Compose the application"""
        initial_data = {
            # Personal info fields (no prefix)
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '555-1234',
            
            # Billing address (prefixed)
            'billing_street': '123 Main St',
            'billing_city': 'Springfield',
            'billing_state': 'IL',
            'billing_postal_code': '62701',
            
            # Shipping address (prefixed)
            'shipping_street': '456 Oak Ave',
            'shipping_city': 'Chicago',
            'shipping_state': 'IL',
            'shipping_postal_code': '60601',
            
            # Additional fields
            'same_as_billing': False,
            'notes': 'Please ring doorbell'
        }
        
        self.form = OrderForm(
            title="Order Form - Composed from Reusable Forms",
            data=initial_data
        )
        yield self.form.render()
    
    def on_form_submitted(self, event):
        """Handle form submission"""
        data = event.form.get_data()
        
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()
        
        # Pass form for field lookup demo
        self.push_screen(
            ResultsScreen("Order Submitted!", data, event.form.form), 
            check_reset
        )
    
    def on_form_cancelled(self, event):
        """Handle form cancellation"""
        def check_reset(should_reset):
            if should_reset:
                self.reset_form()
        
        self.push_screen(ResultsScreen("Order Cancelled", None), check_reset)
    
    def reset_form(self):
        """Clear form and create fresh one"""
        old_form = self.query_one("RenderedForm")
        old_form.remove()
        
        self.form = OrderForm(title="Order Form - Composed from Reusable Forms")
        self.mount(self.form.render())


def main():
    """Run the example"""
    app = ShopApp()
    app.run()


if __name__ == "__main__":
    main()
