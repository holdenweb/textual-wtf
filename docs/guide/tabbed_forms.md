# Tabbed Forms

`TabbedForm` renders multiple `Form` instances as tabs using Textual's `TabbedContent` widget. Each form occupies its own `TabPane`. When any field in a tab has a validation error, that tab's label turns red — giving the user an immediate visual cue about which section needs attention.

## Basic usage

```python title="tabbed_checkout.py"
from textual.app import App, ComposeResult, on
from textual_wtf import Form, StringField, IntegerField, TabbedForm

class PersonalForm(Form):
    title = "Personal Info"

    first_name = StringField("First name", required=True)
    last_name  = StringField("Last name", required=True)
    email      = StringField("Email", required=True)

class ShippingForm(Form):
    title = "Shipping"

    street   = StringField("Street", required=True)
    city     = StringField("City", required=True)
    postcode = StringField("Postcode", required=True)

class PaymentForm(Form):
    title = "Payment"

    card_number = StringField("Card number", required=True, max_length=19)
    expiry      = StringField("Expiry (MM/YY)", required=True, max_length=5)
    cvv         = StringField("CVV", required=True, max_length=4)


class CheckoutApp(App):
    def compose(self) -> ComposeResult:
        self.personal = PersonalForm()
        self.shipping = ShippingForm()
        self.payment  = PaymentForm()

        yield TabbedForm(self.personal, self.shipping, self.payment)
```

Pass form instances as positional arguments to `TabbedForm`. They are rendered in order, each in its own tab.

## Tab titles

The tab label for each form comes from `form.title`. If a form has no title, the fallback is `"Form N"` where `N` is the 1-based position.

Set `title` as a class attribute:

```python
class ShippingForm(Form):
    title = "Shipping"
    ...
```

Or pass it at instantiation to override:

```python
yield TabbedForm(
    PersonalForm(title="Step 1: Personal"),
    ShippingForm(title="Step 2: Shipping"),
    PaymentForm(title="Step 3: Payment"),
)
```

## Error state in tabs

When a field in a tab has a validation error, the tab label gains the CSS class `has-error`, which sets the label colour to `$error` (the theme's error colour, typically red). The class is removed as soon as all errors in that tab are cleared.

This feedback is live — it updates as the user tabs between fields, not only on submit.

```css
/* Built into TabbedForm.DEFAULT_CSS — no action needed */
TabbedForm Tab.has-error {
    color: $error;
}
```

## Handling submit and cancel

Each form inside a `TabbedForm` has its own `DefaultFormLayout` with Submit and Cancel buttons. The `Form.Submitted` and `Form.Cancelled` messages bubble up to the screen.

To validate all tabs before accepting the submission, intercept `Form.Submitted` from any one form and manually validate the others:

```python title="tabbed_checkout.py (continued)"
class CheckoutApp(App):
    ...

    @on(Form.Submitted)
    def on_submitted(self, event: Form.Submitted) -> None:
        # Validate the other two forms as well
        personal_ok = self.personal.clean()
        shipping_ok = self.shipping.clean()
        payment_ok  = self.payment.clean()

        if personal_ok and shipping_ok and payment_ok:
            data = {
                **self.personal.get_data(),
                **self.shipping.get_data(),
                **self.payment.get_data(),
            }
            self.notify(f"Order placed: {data}", severity="information")
        else:
            self.notify("Please fix errors in all tabs.", severity="error")

    @on(Form.Cancelled)
    def on_cancelled(self, event: Form.Cancelled) -> None:
        self.app.exit()
```

!!! tip "Which form was submitted?"
    `event.form` is the specific form instance whose Submit button was pressed. `event.layout` is the `DefaultFormLayout` inside that tab.

## Complete working example

```python title="wizard_app.py"
from textual.app import App, ComposeResult, on
from textual_wtf import (
    Form,
    StringField,
    IntegerField,
    BooleanField,
    EmailValidator,
    TabbedForm,
)


class AccountForm(Form):
    title = "Account"

    username = StringField("Username", required=True, min_length=3, max_length=30)
    email    = StringField(
        "Email",
        required=True,
        validators=[EmailValidator()],
    )
    password = StringField("Password", required=True, min_length=8)


class ProfileForm(Form):
    title = "Profile"

    display_name = StringField("Display name", required=True)
    bio          = StringField("Short bio", max_length=160)
    age          = IntegerField("Age", minimum=13, maximum=120)


class PreferencesForm(Form):
    title = "Preferences"

    newsletter     = BooleanField("Subscribe to newsletter", initial=True)
    beta_features  = BooleanField("Opt in to beta features")


class WizardApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    TabbedForm {
        width: 70;
        max-height: 90%;
        border: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        self.account     = AccountForm()
        self.profile     = ProfileForm()
        self.preferences = PreferencesForm()

        yield TabbedForm(self.account, self.profile, self.preferences)

    @on(Form.Submitted)
    def on_any_submitted(self, event: Form.Submitted) -> None:
        # Only finalize if all forms are valid
        all_valid = all([
            self.account.clean(),
            self.profile.clean(),
            self.preferences.clean(),
        ])
        if all_valid:
            data = {
                **self.account.get_data(),
                **self.profile.get_data(),
                **self.preferences.get_data(),
            }
            self.notify(f"Registered: {data['username']}", severity="information")
        else:
            self.notify(
                "Please complete all tabs before submitting.",
                severity="error",
            )

    @on(Form.Cancelled)
    def on_cancelled(self, event: Form.Cancelled) -> None:
        self.app.exit()


if __name__ == "__main__":
    WizardApp().run()
```

!!! note "Independent validation per tab"
    Each tab's Submit button only validates that tab's form. If you need to enforce that all tabs are complete before any submission is accepted, use the pattern shown above — validate all forms in the `Form.Submitted` handler.
