# Validation

textual-wtf has a unified validation pipeline: the same validators run whether triggered by an interactive event or by an explicit `form.validate()` call. This page explains when validation fires, how to run it manually, and how to implement cross-field validation.

## When validation fires

Each validator has a `validate_on` frozenset that lists the events that trigger it automatically during interaction. There are three events:

`"change"`
:   Fires every time the user modifies the widget value (on each keystroke for `Input`, on each selection change for `Select`, on each checkbox toggle for `Checkbox`).

`"blur"`
:   Fires when the user moves focus away from the widget.

`"submit"`
:   Fires when `form.validate()` (or `form.clean()`) is called — typically when the user presses the Submit button or the Enter key.

The default fire events for built-in validators:

| Validator | validate_on |
|---|---|
| `Required` | `{"blur", "submit"}` |
| `MinLength` | `{"blur", "submit"}` |
| `MaxLength` | `{"change", "blur", "submit"}` |
| `MinValue` | `{"blur", "submit"}` |
| `MaxValue` | `{"change", "blur", "submit"}` |
| `EmailValidator` | `{"blur", "submit"}` |
| `FunctionValidator` | `{"blur", "submit"}` |

!!! note "Submit always runs everything"
    When `form.validate()` is called, **every** validator on every field runs regardless of `validate_on`. The `validate_on` frozenset only gates the interactive (change and blur) paths.

## Validation methods on Form

`form.validate() -> bool`
:   Runs all validators on every field. Returns `True` only if every field passes. Sets error state on any failing bound fields. This is the field-level validation step.

`form.is_valid() -> bool`
:   Alias for `validate()`. Use whichever reads more clearly in your context.

`form.clean() -> bool`
:   Full pipeline: calls `validate()` first, then — if all fields pass — calls `clean_form()` for cross-field logic. Returns `True` only if both steps succeed. Error state from `add_error()` inside `clean_form()` is automatically reflected in the UI.

`form.clean_form() -> bool`
:   Override this method in your form class to implement cross-field validation logic. Return `True` if the form data is valid. Called only after all individual fields have passed `validate()`. Use `self.add_error(field_name, message)` to attach errors to specific fields.

!!! info "DefaultFormLayout uses clean()"
    When the user presses Submit (or Enter) in a `DefaultFormLayout`, the layout calls `form.clean()` — the full pipeline including `clean_form()`. The `Submitted` message is posted only if `clean()` returns `True`.

## Cross-field validation with clean_form()

Override `clean_form()` on your form class. Call `self.add_error(field_name, message)` to attach validation errors to specific fields. Returning `False` alone does not display an error message — use `add_error()` or both.

```python title="password_form.py"
from textual_wtf import Form, StringField

class PasswordChangeForm(Form):
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
        help_text="Re-enter your new password.",
    )

    def clean_form(self) -> bool:
        new_pw  = self.new_password.value
        confirm = self.confirm_password.value

        if new_pw and confirm and new_pw != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
            return False

        return True
```

### add_error()

```python
form.add_error(field_name: str, message: str) -> None
```

- `field_name` must be the fully-qualified name of a field on this form (e.g. `"billing_city"` for an embedded field).
- `message` is the error string shown below the field.
- Calling `add_error()` inside `clean_form()` causes `clean()` to return `False` even if `clean_form()` itself returns `True`.
- Raises `FormError` if the field name does not exist.
- UI updates are applied automatically at the end of `clean()`.

```python
def clean_form(self) -> bool:
    if self.start_date.value and self.end_date.value:
        if self.start_date.value > self.end_date.value:
            self.add_error("end_date", "End date must be after start date.")
            return False
    return True
```

## Error state on BoundField

After validation runs, inspect error state through the `BoundField`:

`bf.has_error: bool`
:   `True` if this field currently has one or more validation errors.

`bf.errors: list[str]`
:   The list of error message strings (may contain more than one if multiple validators failed).

`bf.error_messages: list[str]`
:   Same as `errors` — kept for compatibility. Prefer `errors`.

```python title="inspect_errors.py"
form = MyForm(data={"username": ""})
form.validate()

bf = form.username
if bf.has_error:
    for msg in bf.errors:
        print(msg)
# This field is required.
```

## Running validation manually

You can call `form.validate()` or `form.clean()` at any point — not just from a Submit handler. This is useful for programmatic form submission outside of a layout:

```python
form = SignupForm(data={"username": "alice", "email": "not-an-email"})

if form.clean():
    # All fields valid, cross-field logic passed
    process_signup(form.get_data())
else:
    # Report errors
    for name, bf in form.bound_fields.items():
        if bf.has_error:
            print(f"{name}: {', '.join(bf.errors)}")
```

!!! warning "Headless validation"
    When calling `clean()` outside a Textual app context, error state is updated on the `BoundField` objects but there are no widgets to update. This is fine for testing or background processing — just read errors from `bf.errors` rather than expecting UI updates.

## Validation and the full pipeline

```
User edits field
        │
        ▼
  widget event (Input.Changed, Input.Submitted, etc.)
        │
        ▼
  ControllerAwareLayout or FieldWidget routes event to FieldController
        │
        ▼
  FieldController._validate_for(event_name)
        │  Runs only validators whose validate_on includes this event
        ▼
  Error state updated → FieldWidget error label refreshed
```

```
User presses Submit
        │
        ▼
  FormLayout._do_submit()
        │
        ▼
  form.clean()
     │
     ├─ form.validate()          ← runs ALL validators on ALL fields
     │       │
     │       └─ if all pass ──▶ form.clean_form()
     │                                 │
     │                                 └─ can call add_error()
     │
     └─ if True → post Form.Submitted
        if False → UI shows errors, no message posted
```
