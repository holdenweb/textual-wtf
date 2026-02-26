# TabbedForm

`TabbedForm` renders a sequence of `BaseForm` instances as tabs using Textual's `TabbedContent` widget.

## TabbedForm

::: textual_wtf.tabbed_form.TabbedForm
    options:
      members:
        - __init__
        - compose
        - on_mount
      show_root_heading: true
      show_source: false

### Constructor

```python
def __init__(self, *forms: BaseForm, **kwargs: Any) -> None
```

Pass any number of `BaseForm` instances as positional arguments. They are rendered in order, each in its own `TabPane`.

```python
yield TabbedForm(
    PersonalForm(title="Personal"),
    BillingForm(title="Billing"),
    ShippingForm(title="Shipping"),
)
```

### Tab titles

The tab label for each form is taken from `form.title`. If not set, the label defaults to `"Form N"` (1-based index).

### Error state

When any field in a tab has a validation error, the tab's `Tab` widget gains the CSS class `has-error`. The built-in CSS rules:

```css
TabbedForm Tab.has-error {
    color: $error;
}
```

This state is updated live as the user interacts with fields — errors are reflected immediately when a field loses focus, not only on submit.

### Messages

Each form inside a `TabbedForm` posts its own `Form.Submitted` and `Form.Cancelled` messages when the user interacts with the Submit or Cancel buttons inside that tab. These messages bubble up to the screen as normal.

`event.form` is the specific form instance whose layout was submitted or cancelled. `event.layout` is the `DefaultFormLayout` (or custom layout) inside that tab.

### Default CSS

```css
TabbedForm {
    height: auto;
}
TabbedForm TabbedContent {
    height: auto;
}
TabbedForm TabbedContent > ContentSwitcher {
    height: auto;
}
TabbedForm TabPane {
    height: auto;
    padding: 0;
}
TabbedForm Tab.has-error {
    color: $error;
}
```

## Example

```python title="tabbed_form_example.py"
from textual.app import App, ComposeResult, on
from textual_wtf import Form, StringField, IntegerField, BooleanField, TabbedForm

class AccountForm(Form):
    title = "Account"

    username = StringField("Username", required=True, min_length=3)
    email    = StringField("Email", required=True)

class ProfileForm(Form):
    title = "Profile"

    display_name = StringField("Display name")
    age          = IntegerField("Age", minimum=13)
    public       = BooleanField("Public profile", initial=True)


class MyApp(App):
    CSS = """
    Screen { align: center middle; }
    TabbedForm { width: 70; border: solid $primary; }
    """

    def compose(self) -> ComposeResult:
        self.account = AccountForm()
        self.profile = ProfileForm()
        yield TabbedForm(self.account, self.profile)

    @on(Form.Submitted)
    def on_submitted(self, event: Form.Submitted) -> None:
        # Validate both forms before accepting
        if self.account.clean() and self.profile.clean():
            combined = {**self.account.get_data(), **self.profile.get_data()}
            self.notify(f"Created: {combined['username']}", severity="information")
        else:
            self.notify("Fix errors in all tabs first.", severity="error")

    @on(Form.Cancelled)
    def on_cancelled(self, event: Form.Cancelled) -> None:
        self.app.exit()

if __name__ == "__main__":
    MyApp().run()
```
