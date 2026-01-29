"""Form Composition Example with results display"""
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static
from textual_forms import Form, StringField, BooleanField
from textual_forms.demo.results_screen import ResultsDisplayScreen


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


class ResultsScreen(ResultsDisplayScreen):
    """Utility Screen to display form results with SQL-style field lookup demo"""

    def compose(self) -> ComposeResult:
        with Container(id="results-container"):
            yield Static(self.result_title, id="results-title")

            yield from self.show_data()

            # Demonstrate SQL-style field lookup
            if self.form:
                lookup_lines = [
                    "SQL-Style Field Lookup Examples:",
                    "  get_field('billing_street'): "
                    + self.form.get_field('billing_street').label,
                    f"        [{self.form.get_field('billing_street').value}]",
                    "  get_field('email'): "
                    + self.form.get_field('email').label
                    + " (unqualified)",
                    f"        [{self.form.get_field('email').value}]",
                    "",
                    "Note: In this case get_field('street') would raise AmbiguousFieldError",
                    "      because both billing_street and shipping_street exist",
                ]
                yield Static("\n".join(lookup_lines), id="field-lookup")

            yield from self.buttons()


class ShopScreen(Screen):
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

        def check_reset(cont):
            if cont:
                self.reset_form()
            else:
                self.dismiss(cont)

        # Pass form for field lookup demo
        self.app.push_screen(
            ResultsScreen("Order Submitted!", data, event.form.form), check_reset
        )

    def on_form_cancelled(self, event):
        """Handle form cancellation"""

        def check_reset(cont):
            if cont:
                self.reset_form()
            else:
                self.dismiss(cont)

        self.app.push_screen(ResultsScreen("Order Cancelled", None), check_reset)

    def reset_form(self):
        """Clear form and create fresh one"""
        old_form = self.query_one("RenderedForm")
        old_form.remove()

        self.form = OrderForm(title="Order Form - Composed from Reusable Forms")
        self.mount(self.form.render())


class ShopApp(App):

    def compose(self):
        yield ShopScreen()


def main():
    """Run the example"""
    app = ShopApp()
    app.run()


if __name__ == "__main__":
    main()
