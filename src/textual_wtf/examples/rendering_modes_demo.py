"""
Rendering modes demo: all three ways to render a field, side by side.

  Left   — form.layout()           Automatic DefaultFormLayout. Zero compose code.
  Middle — bf.simple_layout()      Per-field FieldWidget chrome, label_style="beside".
  Right  — bf() + FieldErrors      Raw widget with an explicit FieldErrors label.

All three panels use separate ContactForm instances so they validate
independently.  Submitting any panel shows the resulting data dict.

Run with: python -m examples  (select "Rendering Modes")
"""

from __future__ import annotations

from textual.app import ComposeResult, on
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Button, Label, Static

from textual_wtf import (
    ControllerAwareLayout,
    FieldErrors,
    Form,
    IntegerField,
    StringField,
)

from .example_screen import ExampleScreen


# ── Form definition ───────────────────────────────────────────────────────────


class ContactForm(Form):
    """Simple contact form used identically by all three rendering panels."""

    name = StringField(
        "Name",
        required=True,
        min_length=2,
        max_length=30,
        help_text="Your full name (2–30 characters)",
    )
    email = StringField(
        "Email",
        required=True,
        help_text="Contact email address",
    )
    age = IntegerField(
        "Age",
        minimum=1,
        maximum=120,
        help_text="Age in years",
    )


# ── Custom layout classes ─────────────────────────────────────────────────────


class BesideLayout(ControllerAwareLayout):
    """Middle panel: renders each field via simple_layout() with beside-style labels.

    ``label_style="beside"`` is passed at the call site, demonstrating that
    ``simple_layout()`` can override the form's default label style on a
    per-render basis without changing the form definition.
    """

    DEFAULT_CSS = """
    BesideLayout { height: auto; padding: 1 2; }
    BesideLayout #buttons { height: auto; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        for _, bf in self.form.bound_fields.items():
            yield bf.simple_layout(label_style="beside")
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")


class RawWidgetLayout(ControllerAwareLayout):
    """Right panel: raw bf() widgets paired with explicit FieldErrors labels.

    This is the low-level rendering path for complete layout freedom.
    ``ControllerAwareLayout`` routes widget change/blur events to the correct
    ``FieldController`` automatically based on the ``._field_controller``
    attribute stamped on each widget by ``bf()``.

    ``FieldErrors`` registers with its controller on mount and updates itself
    whenever the error state changes — no manual wiring needed.
    """

    DEFAULT_CSS = """
    RawWidgetLayout { height: auto; padding: 1 2; }
    RawWidgetLayout .raw-label { text-style: bold; margin-top: 1; }
    RawWidgetLayout #buttons { height: auto; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        for _, bf in self.form.bound_fields.items():
            yield Label(bf.label, classes="raw-label")
            yield bf()
            yield FieldErrors(bf.controller)
        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")


# ── Demo screen ───────────────────────────────────────────────────────────────


class RenderingModesDemoScreen(ExampleScreen):
    """Three panels, one form class, three rendering modes."""

    CSS = """
    RenderingModesDemoScreen { layout: vertical; align: left top; }

    #heading {
        width: 100%;
        height: auto;
        text-align: center;
        text-style: bold;
        background: $panel;
        color: $text;
        padding: 1;
    }

    #panels {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    .panel {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        margin: 0 1;
    }

    .panel-title {
        background: $primary;
        color: $text;
        text-style: bold;
        padding: 0 1;
        text-align: center;
    }

    .panel-subtitle {
        color: $text-muted;
        text-align: center;
        padding: 0 1;
        margin-bottom: 1;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        # Three independent form instances so each panel validates separately.
        self.form_auto = ContactForm()
        self.form_simple = ContactForm()
        self.form_raw = ContactForm()

        yield Static("Three ways to render the same form", id="heading")

        with Horizontal(id="panels"):

            # ── Left: fully automatic via form.layout() ──────────────────
            with ScrollableContainer(classes="panel"):
                yield Static("form.layout()", classes="panel-title")
                yield Static("Automatic — zero compose code", classes="panel-subtitle")
                yield self.form_auto.layout()

            # ── Middle: explicit per-field simple_layout() ────────────────
            with ScrollableContainer(classes="panel"):
                yield Static("bf.simple_layout()", classes="panel-title")
                yield Static("FieldWidget chrome, label_style='beside'", classes="panel-subtitle")
                yield self.form_simple.layout(BesideLayout)

            # ── Right: raw bf() widget + explicit FieldErrors ─────────────
            with ScrollableContainer(classes="panel"):
                yield Static("bf() + FieldErrors", classes="panel-title")
                yield Static("Raw widget, explicit error label", classes="panel-subtitle")
                yield self.form_raw.layout(RawWidgetLayout)

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        form = event.form
        if form is self.form_auto:
            source = "Auto"
        elif form is self.form_simple:
            source = "Simple"
        else:
            source = "Raw"
        data = form.get_data()
        self.notify(f"[{source}] {data}", severity="information", timeout=8)

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Cancelled", severity="warning")
        self.action_back()
