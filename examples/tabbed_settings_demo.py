"""
Tabbed settings editor: TabbedForm, set_data(), get_data(), and all field types.

Demonstrates:

- ``TabbedForm`` renders multiple Form instances as TabbedContent tabs.  The
  tab label turns red whenever any field in that tab has a validation error,
  giving immediate feedback about which tab needs attention.

- ``set_data()`` pre-populates all forms from a single settings dict *before*
  any widgets are mounted.  The layout reads ``controller.value`` at widget-
  construction time, so initial values appear correctly without any special
  mounting logic.

- A single Save/Cancel button pair drives the whole multi-tab form.  Each
  form's ``clean()`` is called in turn; if any fail, the user is told to
  check all tabs.  ``get_data()`` collects the results from all forms after
  validation and the dicts are merged.

- All five field types appear across the three tabs:
    StringField, IntegerField, BooleanField, ChoiceField, TextField.

- ``SettingsTabLayout`` is a minimal ``ControllerAwareLayout`` subclass that
  suppresses the default Enter-to-submit / Escape-to-cancel bindings so the
  single external Save button has unambiguous ownership.

- The right panel shows the original settings and (after saving) the newly
  saved settings, making the data round-trip visible.

- ``label_style = "placeholder"`` on each form class moves field labels into
  the ``Input`` placeholder, removing the above-label row for text inputs and
  saving vertical space.  ``help_style = "tooltip"`` moves ``help_text`` off
  the screen entirely — it appears as a hover tooltip instead.

Run with: python -m examples  (select "Tabbed Settings")
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Static

from textual_wtf import (
    BooleanField,
    ChoiceField,
    ControllerAwareLayout,
    Form,
    IntegerField,
    StringField,
    TabbedForm,
    TextField,
)

from .example_screen import ExampleScreen


# ── Shared tab layout ─────────────────────────────────────────────────────────


class SettingsTabLayout(ControllerAwareLayout):
    """Fields-only layout for use inside TabbedForm.

    Removes the Submit/Cancel buttons and keyboard bindings that
    ``DefaultFormLayout`` would add — a single Save button lives outside the
    ``TabbedForm`` widget and owns those actions instead.
    """

    BINDINGS = []  # suppress Enter-to-submit / Escape-to-cancel inside each tab

    DEFAULT_CSS = """
    SettingsTabLayout { height: auto; padding: 1 2; }
    """

    def compose(self) -> ComposeResult:
        for _, bf in self.form.bound_fields.items():
            yield bf.simple_layout()


# ── Form definitions ──────────────────────────────────────────────────────────


class ProfileForm(Form):
    """Profile tab: StringField and TextField."""

    title = "Profile"
    layout_class = SettingsTabLayout
    label_style = "placeholder"
    help_style = "tooltip"

    username = StringField(
        "Username",
        required=True,
        min_length=3,
        max_length=30,
        help_text="Unique display name (3–30 characters)",
    )
    email = StringField(
        "Email",
        required=True,
        help_text="Contact email address",
    )
    bio = TextField(
        "Bio",
        max_length=200,
        help_text="Short biography (up to 200 characters)",
    )


class PreferencesForm(Form):
    """Preferences tab: ChoiceField, BooleanField, IntegerField."""

    title = "Preferences"
    layout_class = SettingsTabLayout
    label_style = "placeholder"
    help_style = "tooltip"

    theme = ChoiceField(
        "Theme",
        choices=[("Dark", "dark"), ("Light", "light"), ("Auto", "auto")],
        help_text="UI colour scheme",
    )
    notifications = BooleanField(
        "Enable notifications",
        help_text="Receive in-app alerts",
    )
    page_size = IntegerField(
        "Page size",
        minimum=5,
        maximum=200,
        help_text="Items per page (5–200)",
    )


class AccessibilityForm(Form):
    """Accessibility tab: BooleanField and IntegerField."""

    title = "Accessibility"
    layout_class = SettingsTabLayout
    label_style = "placeholder"
    help_style = "tooltip"

    high_contrast = BooleanField(
        "High contrast mode",
        help_text="Increase foreground/background contrast",
    )
    font_size = IntegerField(
        "Font size",
        minimum=10,
        maximum=24,
        help_text="UI font size in points (10–24)",
    )
    reduce_motion = BooleanField(
        "Reduce motion",
        help_text="Minimise animations and transitions",
    )


# ── Initial data ──────────────────────────────────────────────────────────────

INITIAL_SETTINGS: dict = {
    # Profile
    "username": "sholden",
    "email": "steve@holdenweb.com",
    "bio": "Python developer and Textual enthusiast.",
    # Preferences
    "theme": "dark",
    "notifications": True,
    "page_size": 25,
    # Accessibility
    "high_contrast": False,
    "font_size": 14,
    "reduce_motion": False,
}


# ── Demo screen ───────────────────────────────────────────────────────────────


class TabbedSettingsDemoScreen(ExampleScreen):
    """Multi-tab settings editor: TabbedForm + set_data() + get_data()."""

    CSS = """
    TabbedSettingsDemoScreen { layout: vertical; align: left top; }

    #main {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    #editor-col {
        width: 2fr;
        height: 100%;
        padding: 1 2;
    }

    #right-col {
        width: 1fr;
        height: 100%;
        border-left: solid $accent;
        padding: 1 2;
    }

    #save-row {
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    #save-row Button { margin-right: 1; }

    .data-heading {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    #original-data, #saved-data {
        height: auto;
        min-height: 3;
        border: solid $panel;
        padding: 1;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        self.profile_form = ProfileForm()
        self.prefs_form = PreferencesForm()
        self.access_form = AccessibilityForm()

        # Pre-populate all forms before any widgets are mounted.
        # set_data() updates controller values; the layout reads them at
        # widget-construction time, so initial values appear correctly.
        for form in (self.profile_form, self.prefs_form, self.access_form):
            form.set_data(INITIAL_SETTINGS)

        with Horizontal(id="main"):

            # ── Left: TabbedForm + Save/Cancel ────────────────────────────
            with Vertical(id="editor-col"):
                yield TabbedForm(
                    self.profile_form,
                    self.prefs_form,
                    self.access_form,
                )
                with Horizontal(id="save-row"):
                    yield Button("Save", id="save-btn", variant="primary")
                    yield Button("Cancel", id="cancel-btn")

            # ── Right: data panels ────────────────────────────────────────
            with ScrollableContainer(id="right-col"):
                yield Static("Original settings", classes="data-heading")
                yield Static(
                    self._format_data(INITIAL_SETTINGS),
                    id="original-data",
                )
                yield Static("Saved settings", classes="data-heading")
                yield Static(
                    "(press Save to update)",
                    id="saved-data",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._save()
        elif event.button.id == "cancel-btn":
            self.action_back()

    def _save(self) -> None:
        """Validate all tabs and collect data if everything is clean."""
        forms = (self.profile_form, self.prefs_form, self.access_form)

        # Call clean() on every form even if an earlier one fails, so all
        # error states are updated and all red tab indicators are visible.
        results = [form.clean() for form in forms]

        if all(results):
            data: dict = {}
            for form in forms:
                data.update(form.get_data())
            self.query_one("#saved-data", Static).update(self._format_data(data))
            self.notify("Settings saved!", severity="information", timeout=5)
        else:
            self.notify(
                "One or more fields have errors — check all tabs.",
                severity="error",
                timeout=5,
            )

    @staticmethod
    def _format_data(data: dict) -> str:
        return "\n".join(f"{k}: {v!r}" for k, v in data.items())
