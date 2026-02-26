# How-to: Cross-field Validation

Some validation rules depend on the values of multiple fields simultaneously — for example, confirming a password, checking that an end date is after a start date, or verifying that a total quantity matches a sum of parts.

Use `clean_form()` together with `add_error()` to implement this kind of logic.

## Password confirmation

The most common example: a "new password" field and a "confirm password" field that must match.

```python title="password_form.py"
from textual.app import App, ComposeResult, on
from textual_wtf import Form, StringField


class PasswordChangeForm(Form):
    title = "Change Password"

    current_password = StringField(
        "Current password",
        required=True,
        help_text="Your existing password.",
    )
    new_password = StringField(
        "New password",
        required=True,
        min_length=8,
        help_text="Minimum 8 characters.",
    )
    confirm_password = StringField(
        "Confirm new password",
        required=True,
        help_text="Type your new password again.",
    )

    def clean_form(self) -> bool:
        new_pw  = self.new_password.value
        confirm = self.confirm_password.value

        # Only compare if both fields have values
        # (Required validators handle the empty-field case)
        if new_pw and confirm and new_pw != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
            return False

        return True
```

When the user submits the form:

1. `form.validate()` runs all field-level validators (Required, MinLength, etc.).
2. If all pass, `clean_form()` is called.
3. If the passwords differ, `add_error("confirm_password", "Passwords do not match.")` attaches the error to the confirm field.
4. The form returns `False` from `clean()` and the `Submitted` message is not posted.

!!! note "clean_form() is called only after all fields pass"
    If `new_password` fails `MinLength`, `clean_form()` is never called. The length error on `new_password` is shown, but the confirmation check is deferred until the individual fields are valid.

## Date range validation

```python title="booking_form.py"
from datetime import date
from textual_wtf import Form, StringField, ValidationError


def parse_date(value: str) -> date | None:
    """Simple YYYY-MM-DD parser for demonstration."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError("Enter a date in YYYY-MM-DD format.")


class BookingForm(Form):
    title = "Make a Booking"

    name = StringField("Guest name", required=True)
    check_in  = StringField(
        "Check-in date",
        required=True,
        validators=[parse_date],
        help_text="Format: YYYY-MM-DD",
    )
    check_out = StringField(
        "Check-out date",
        required=True,
        validators=[parse_date],
        help_text="Format: YYYY-MM-DD",
    )

    def clean_form(self) -> bool:
        try:
            check_in  = date.fromisoformat(self.check_in.value or "")
            check_out = date.fromisoformat(self.check_out.value or "")
        except ValueError:
            # Individual field validators already caught this
            return False

        if check_out <= check_in:
            self.add_error(
                "check_out",
                "Check-out must be at least one day after check-in.",
            )
            return False

        return True
```

## Multiple errors in one clean_form()

You can call `add_error()` multiple times to attach errors to different fields. Each call contributes to the error state; `clean()` returns `False` as soon as any `add_error()` has been called.

```python title="budget_form.py"
from textual_wtf import Form, IntegerField


class BudgetForm(Form):
    total_budget   = IntegerField("Total budget ($)", required=True, minimum=0)
    marketing_cost = IntegerField("Marketing ($)", required=True, minimum=0)
    dev_cost       = IntegerField("Development ($)", required=True, minimum=0)
    ops_cost       = IntegerField("Operations ($)", required=True, minimum=0)

    def clean_form(self) -> bool:
        total      = self.total_budget.value
        components = [
            self.marketing_cost.value,
            self.dev_cost.value,
            self.ops_cost.value,
        ]

        if None in [total, *components]:
            return False  # individual fields handle the empty-value errors

        component_sum = sum(components)
        is_valid = True

        if component_sum > total:
            self.add_error(
                "total_budget",
                f"Component costs (${component_sum}) exceed the total budget (${total}).",
            )
            is_valid = False

        if self.marketing_cost.value > total * 0.5:
            self.add_error(
                "marketing_cost",
                "Marketing cannot exceed 50% of the total budget.",
            )
            is_valid = False

        return is_valid
```

## Complete runnable example

```python title="password_change_app.py"
from textual.app import App, ComposeResult, on
from textual_wtf import Form, StringField


class PasswordChangeForm(Form):
    title = "Change Password"

    current_password = StringField(
        "Current password",
        required=True,
    )
    new_password = StringField(
        "New password",
        required=True,
        min_length=8,
        help_text="Minimum 8 characters.",
    )
    confirm_password = StringField(
        "Confirm new password",
        required=True,
    )

    def clean_form(self) -> bool:
        new_pw  = self.new_password.value
        confirm = self.confirm_password.value
        if new_pw and confirm and new_pw != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
            return False
        return True


class PasswordApp(App):
    CSS = """
    Screen { align: center middle; }
    DefaultFormLayout { width: 50; border: solid $primary; }
    """

    def compose(self) -> ComposeResult:
        self.form = PasswordChangeForm()
        yield self.form.build_layout()

    @on(PasswordChangeForm.Submitted)
    def on_submitted(self, event: PasswordChangeForm.Submitted) -> None:
        # In a real app, verify current_password and update the stored hash
        self.notify("Password changed successfully.", severity="information")

    @on(PasswordChangeForm.Cancelled)
    def on_cancelled(self, event: PasswordChangeForm.Cancelled) -> None:
        self.app.exit()


if __name__ == "__main__":
    PasswordApp().run()
```

## Tips

!!! tip "Guard against None in clean_form()"
    `clean_form()` is only called after all field validators pass. But `required=False` fields may still have `None` values. Always check for `None` before comparing or computing with field values.

!!! warning "Do not access widget state directly"
    Inside `clean_form()`, read values through `self.<field_name>.value` (the `BoundField`) not through Textual widget queries. The widget may not be mounted when `clean()` is called programmatically.

!!! tip "add_error() vs. returning False"
    `add_error()` attaches a visible error message to a specific field widget. Returning `False` without calling `add_error()` causes `clean()` to fail silently — the user won't see why their submission was rejected. Always pair a `return False` with at least one `add_error()` call.
