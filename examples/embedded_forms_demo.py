"""
Example demonstrating embedded forms — a single Form class whose fields come
from nested Form subclass assignments.

Shows:
- Assigning a Form subclass to a class variable inside another Form.  The
  metaclass flattens the inner form's fields into the parent, prefixed with
  the variable name and an underscore (billing_street, shipping_city, etc.).
- That unqualified attribute access (form.street) resolves when unambiguous,
  and raises AmbiguousFieldError when the same suffix appears in multiple
  embedded forms.
- An interactive field-path lookup where the user can type a field name
  and see how it resolves (or why it fails).

Run with: python -m examples  (select "Embedded Forms")
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical

from .example_screen import ExampleScreen
from textual.widgets import Button, Input, Static, TabbedContent, TabPane
from textual_wtf import Form, StringField
from textual_wtf.exceptions import AmbiguousFieldError


class AddressForm(Form):
    """Reusable postal address form (embedded into OrderForm twice)."""

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


class OrderForm(Form):
    """Composite form: personal fields + two embedded address sub-forms."""

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

    billing = AddressForm
    shipping = AddressForm


class EmbeddedFormsDemoScreen(ExampleScreen):
    """Screen with a single OrderForm rendered across panels and tabs."""

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
        self.form = OrderForm()
        bf = self.form.bound_fields

        with ScrollableContainer(id="outer-scroll"):
            with Horizontal(id="forms-row"):
                with Vertical(classes="form-panel"):
                    yield Static("personal", classes="panel-title")
                    yield bf["name"].simple_layout()
                    yield bf["email"].simple_layout()
                with Vertical(classes="form-panel"):
                    yield Static("addresses", classes="panel-title")
                    with TabbedContent():
                        with TabPane("Billing", id="billing-tab"):
                            yield bf["billing_street"].simple_layout()
                            yield bf["billing_city"].simple_layout()
                            yield bf["billing_postcode"].simple_layout()
                        with TabPane("Shipping", id="shipping-tab"):
                            yield bf["shipping_street"].simple_layout()
                            yield bf["shipping_city"].simple_layout()
                            yield bf["shipping_postcode"].simple_layout()

            with Vertical(id="query-section"):
                yield Static("Field Lookup", id="query-title")
                yield Static(
                    "Type a field name to inspect it.  Try qualified names "
                    "(billing_street), unqualified (name), or ambiguous "
                    "(street).",
                    id="query-hint",
                )
                with Horizontal(id="query-row"):
                    yield Input(
                        placeholder="billing_street  /  name  /  street",
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
        """Resolve a field name via the form's attribute access."""
        if not path:
            names = ", ".join(self.form.bound_fields)
            return f"All fields on OrderForm:\n  {names}"

        # Try the form's own __getattr__ resolution — this handles
        # qualified names, unqualified unambiguous, and ambiguous cases.
        try:
            bf = self.form.get_field(path)
        except AmbiguousFieldError as exc:
            return (
                f"'{exc.name}' is ambiguous — it matches multiple "
                f"embedded fields:\n  {', '.join(exc.candidates)}\n"
                f"Use the full prefixed name instead."
            )
        except AttributeError:
            names = ", ".join(self.form.bound_fields)
            return (
                f"No field '{path}' on OrderForm.\n"
                f"Available: {names}"
            )

        try:
            value = self.form.get_data().get(bf.name)
            value_repr = repr(value)
        except Exception:
            value_repr = "(error reading value)"

        errors = bf.errors
        lines = [
            f"  name      {bf.name}",
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
