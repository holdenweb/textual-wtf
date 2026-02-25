"""
Example demonstrating embedded forms — multiple Form instances in one screen.

Shows:
- A PersonalForm and two AddressForm instances (billing, shipping) embedded
  in a shared screen layout; the address forms live inside a TabbedContent
  so the user can switch between them without leaving the screen.
- That each form has its own field namespace, distinct from the others.
- An interactive field-path lookup: type a path such as  personal.name  or
  billing.street  (or just  name  to auto-search all forms) and inspect the
  field's current value and validation state — or see why the path fails.
  Unqualified names like  street  that appear in multiple forms surface the
  ambiguity and prompt for the qualified form.

Run with: python -m examples  (select "Embedded Forms")
"""

from textual.app import ComposeResult, on
from textual.containers import Horizontal, ScrollableContainer, Vertical

from .example_screen import ExampleScreen
from textual.widgets import Button, Input, Static, TabbedContent, TabPane
from textual_wtf import Form, StringField


class PersonalForm(Form):
    """Personal details sub-form."""

    label_style = "beside"
    help_style = "tooltip"

    name = StringField(
        label="Name",
        required=True,
        min_length=2,
        help_text="Given and family name",
    )
    email = StringField(
        label="Email",
        required=True,
        help_text="Contact email address",
    )


class AddressForm(Form):
    """Postal address sub-form (reused for billing and shipping)."""

    label_style = "beside"
    help_style = "tooltip"

    street = StringField(
        label="Street",
        required=True,
        help_text="House number and street name",
    )
    city = StringField(
        label="City",
        required=True,
        help_text="Town or city",
    )
    postcode = StringField(
        label="Postcode",
        help_text="Postal / zip code",
    )


class EmbeddedFormsDemoScreen(ExampleScreen):
    """Screen with embedded forms and a live field-path lookup tool."""

    CSS = """
    Screen {
        layout: vertical;
        align: left top;
    }

    #outer-scroll {
        height: 1fr;
        width: 100%;
    }

    #forms-row {
        layout: horizontal;
        height: auto;
        padding: 1 1 0 1;
    }

    .form-panel {
        width: 1fr;
        height: auto;
        border: solid $primary;
        margin: 0 1;
        padding: 1 2;
    }

    .panel-title {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
        text-align: center;
    }

    TabbedContent {
        height: auto;
    }

    TabbedContent > ContentSwitcher {
        height: auto;
    }

    TabPane {
        height: auto;
        padding: 0;
    }

    #query-section {
        height: auto;
        border: double $accent;
        margin: 1 2;
        padding: 1 2;
    }

    #query-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #query-hint {
        color: $text-muted;
        margin-bottom: 1;
    }

    #query-row {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

    #query-input {
        width: 1fr;
    }

    #lookup-btn {
        width: auto;
        margin-left: 1;
    }

    #query-result {
        height: auto;
        min-height: 3;
        border: solid $panel;
        padding: 1;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        self.personal_form = PersonalForm()
        self.billing_form = AddressForm()
        self.shipping_form = AddressForm()
        self._forms = {
            "personal": self.personal_form,
            "billing": self.billing_form,
            "shipping": self.shipping_form,
        }

        with ScrollableContainer(id="outer-scroll"):
            with Horizontal(id="forms-row"):
                with Vertical(classes="form-panel"):
                    yield Static("personal", classes="panel-title")
                    yield self.personal_form.build_layout()
                with Vertical(classes="form-panel"):
                    yield Static("addresses", classes="panel-title")
                    with TabbedContent():
                        with TabPane("Billing", id="billing-tab"):
                            yield self.billing_form.build_layout()
                        with TabPane("Shipping", id="shipping-tab"):
                            yield self.shipping_form.build_layout()

            with Vertical(id="query-section"):
                yield Static("Field Lookup", id="query-title")
                yield Static(
                    "Enter a field path to inspect its current value and "
                    "validation state.\n"
                    "Examples:  personal.name   billing.street   shipping.city"
                    "   street  (unqualified searches all forms)",
                    id="query-hint",
                )
                with Horizontal(id="query-row"):
                    yield Input(
                        placeholder="personal.name  /  billing.street  /  street",
                        id="query-input",
                    )
                    yield Button("Look up", variant="primary", id="lookup-btn")
                yield Static(
                    "Results will appear here.",
                    id="query-result",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lookup-btn":
            self._do_lookup()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Trigger lookup when Enter is pressed in the query box."""
        if event.input.id == "query-input":
            self._do_lookup()

    def _do_lookup(self) -> None:
        path = self.query_one("#query-input", Input).value.strip()
        result = self._resolve(path)
        self.query_one("#query-result", Static).update(result)

    def _resolve(self, path: str) -> str:
        """Resolve a field path and return a human-readable description."""
        if not path:
            return "Available field paths:\n  " + ",  ".join(self._all_paths())

        if "." in path:
            form_name, _, field_name = path.partition(".")
            return self._lookup(form_name, field_name)

        # Unqualified name — search all forms
        found = [
            form_name
            for form_name, form in self._forms.items()
            if path in form.bound_fields
        ]
        if not found:
            return (
                f"Field '{path}' not found in any form.\n"
                f"All paths: {', '.join(self._all_paths())}"
            )
        if len(found) > 1:
            return (
                f"'{path}' exists in multiple forms: {', '.join(found)}.\n"
                f"Use qualified syntax, e.g.  {found[0]}.{path}"
            )
        return self._lookup(found[0], path)

    def _lookup(self, form_name: str, field_name: str) -> str:
        """Look up a specific form.field and describe it."""
        form = self._forms.get(form_name)
        if form is None:
            available = ",  ".join(self._forms)
            return (
                f"No form named '{form_name}'.\n"
                f"Available forms:  {available}"
            )

        bf = form.bound_fields.get(field_name)
        if bf is None:
            available = ",  ".join(form.bound_fields)
            return (
                f"Form '{form_name}' has no field '{field_name}'.\n"
                f"Fields in '{form_name}':  {available}"
            )

        try:
            value = form.get_data().get(field_name)
            value_repr = repr(value)
        except Exception:
            value_repr = "(error reading value — field may contain invalid data)"

        errors = bf.errors
        lines = [
            f"  path      {form_name}.{field_name}",
            f"  label     {bf._field.label!r}",
            f"  required  {bf._field.required}",
            f"  value     {value_repr}",
        ]
        if errors:
            lines += [f"  error     {e}" for e in errors]
        else:
            lines.append(
                "  errors    (none — tab away from a field to trigger validation)"
            )
        return "\n".join(lines)

    def _all_paths(self) -> list[str]:
        return [
            f"{form_name}.{field_name}"
            for form_name, form in self._forms.items()
            for field_name in form.bound_fields
        ]

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        if event.form.is_valid():
            data = event.form.get_data()
            self.notify(f"Submitted: {data}", severity="information")
        else:
            self.notify("Please fix validation errors first", severity="error")

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Form cancelled", severity="warning")
        self.action_back()
