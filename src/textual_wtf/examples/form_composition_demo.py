"""
Form composition demo: embedding sub-forms to build composite field sets.

Demonstrates:

- Assigning a Form subclass *instance* to a class variable on another Form.
  The metaclass flattens the inner fields with the variable name as a prefix:
  ``billing = AddressForm()`` produces ``billing_street``, ``billing_city``,
  ``billing_postcode`` on the outer form.

- Passing ``required=False`` on the embedded instance to make all of its
  fields optional without touching the sub-form class itself.  Field-level
  ``required=`` settings always win; the instance-level override only applies
  to fields that didn't set it explicitly.

- A ``CheckoutLayout`` custom ControllerAwareLayout that arranges personal
  and address fields in labelled sections — a typical real-world layout that
  ``form.layout()`` alone cannot express.

- The "Copy billing → shipping" button shows the get_data() / set_data()
  round-trip: billing values are extracted, mapped to shipping keys, and the
  form widget is rebuilt from the updated data dict (the same pattern used by
  the interactive layout demo's rebuild-on-style-change).

Run with: python -m examples  (select "Form Composition")
"""

from __future__ import annotations

from textual.app import ComposeResult, on
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Static

from textual_wtf import ControllerAwareLayout, Form, StringField

from .example_screen import ExampleScreen


# ── Sub-form ──────────────────────────────────────────────────────────────────


class AddressForm(Form):
    """Reusable postal address sub-form.

    ``required = True`` is the class-level default, making all address fields
    required when embedded without an override.  The shipping embedding below
    overrides this with ``required=False`` so every shipping field is optional.
    """

    required = True

    street = StringField(
        "Street",
        help_text="House number and street name",
    )
    city = StringField(
        "City",
        help_text="Town or city",
    )
    postcode = StringField(
        "Postcode",
        help_text="Postal / zip code",
    )


# ── Composite form ────────────────────────────────────────────────────────────


class CheckoutForm(Form):
    """Checkout form: personal details + two embedded address sub-forms.

    ``billing = AddressForm()``                 — required (inherits class default)
    ``shipping = AddressForm(required=False)``   — every shipping field is optional

    The flat field dict on this form will contain:
        name, email,
        billing_street, billing_city, billing_postcode,
        shipping_street, shipping_city, shipping_postcode
    """

    label_style = "beside"
    help_style = "tooltip"

    name = StringField(
        "Name",
        required=True,
        min_length=2,
        help_text="Given and family name",
    )
    email = StringField(
        "Email",
        required=True,
        help_text="Contact email address",
    )

    billing = AddressForm()                 # required=True (class-level default)
    shipping = AddressForm(required=False)  # all shipping fields optional


# ── Custom layout ─────────────────────────────────────────────────────────────


class CheckoutLayout(ControllerAwareLayout):
    """Renders CheckoutForm in labelled sections (personal / billing / shipping).

    Accessing fields by their prefixed names (``bf["billing_street"]``) is the
    normal way to work with embedded form fields in a manual layout.
    """

    DEFAULT_CSS = """
    CheckoutLayout { height: auto; padding: 0 1; }
    CheckoutLayout .section-title {
        text-style: bold;
        background: $boost;
        color: $text;
        padding: 0 1;
        margin-top: 1;
        margin-bottom: 0;
    }
    CheckoutLayout #buttons { height: auto; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        bf = self.form.bound_fields

        yield Static("Personal", classes="section-title")
        yield bf["name"].simple_layout()
        yield bf["email"].simple_layout()

        yield Static("Billing address (required)", classes="section-title")
        yield bf["billing_street"].simple_layout()
        yield bf["billing_city"].simple_layout()
        yield bf["billing_postcode"].simple_layout()

        yield Static("Shipping address (optional)", classes="section-title")
        yield bf["shipping_street"].simple_layout()
        yield bf["shipping_city"].simple_layout()
        yield bf["shipping_postcode"].simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")


# ── Demo screen ───────────────────────────────────────────────────────────────


class FormCompositionDemoScreen(ExampleScreen):
    """Checkout form with two embedded address sub-forms.

    The right column lists all field names on the flat form (showing the
    prefix convention) and displays ``get_data()`` output after submission.
    """

    CSS = """
    FormCompositionDemoScreen { layout: vertical; align: left top; }

    #main-split {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    #left-col { width: 2fr; height: 100%; }

    #right-col {
        width: 1fr;
        height: 100%;
        border-left: solid $accent;
        padding: 1 2;
    }

    .sidebar-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    #copy-btn { width: 100%; margin-bottom: 1; }

    #result-panel {
        height: auto;
        min-height: 5;
        border: solid $panel;
        padding: 1;
        background: $surface;
        color: $text-muted;
    }

    #field-names {
        color: $text-muted;
        margin-top: 1;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = CheckoutForm()

        # Snapshot field names before any widgets are mounted.
        field_list = "\n  ".join(self.form.bound_fields)

        with Horizontal(id="main-split"):

            # ── Left: scrollable form ─────────────────────────────────────
            with ScrollableContainer(id="left-col"):
                with Vertical(id="form-container"):
                    yield self.form.layout(CheckoutLayout)

            # ── Right: sidebar ────────────────────────────────────────────
            with Vertical(id="right-col"):
                yield Static("Actions", classes="sidebar-title")
                yield Button(
                    "Copy billing → shipping",
                    id="copy-btn",
                    variant="default",
                )
                yield Static("Submitted data", classes="sidebar-title")
                yield Static(
                    "Submit the form to see get_data() here.",
                    id="result-panel",
                )
                yield Static(
                    f"Fields on CheckoutForm:\n  {field_list}",
                    id="field-names",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy-btn":
            self._copy_billing_to_shipping()

    def _copy_billing_to_shipping(self) -> None:
        """Copy billing address values into shipping fields and rebuild the form.

        Uses get_data() to snapshot the current values, maps billing_* keys to
        shipping_* equivalents, then creates a fresh CheckoutForm pre-populated
        with the merged data and mounts it in place of the old layout widget.
        """
        data = self.form.get_data()
        for field in ("street", "city", "postcode"):
            data[f"shipping_{field}"] = data.get(f"billing_{field}")

        self.form = CheckoutForm(data=data)
        container = self.query_one("#form-container")
        container.remove_children()
        container.mount(self.form.layout(CheckoutLayout))
        self.notify("Billing address copied to shipping.", timeout=3)

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        data = event.form.get_data()
        lines = [f"{k}: {v!r}" for k, v in data.items()]
        self.query_one("#result-panel", Static).update("\n".join(lines))
        self.notify("Order submitted!", severity="information", timeout=5)

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Cancelled", severity="warning")
        self.action_back()
