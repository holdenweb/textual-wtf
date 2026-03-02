"""Integration tests using Textual's app.run_test() for UI interaction."""

import pytest

from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Label, Select, TextArea

from textual_wtf import (
    BooleanField,
    BoundField,
    ChoiceField,
    DefaultFormLayout,
    FieldWidget,
    Form,
    IntegerField,
    StringField,
    TextField,
)
from textual_wtf.forms import BaseForm


# ── Test forms ──────────────────────────────────────────────────


class SimpleForm(Form):
    title = "Simple Form"
    name = StringField("Name", required=True)
    age = IntegerField("Age", minimum=0, maximum=150)


class HelpTextForm(Form):
    email = StringField("Email", help_text="Enter your email address")
    name = StringField("Name", help_text="Full name", help_style="tooltip")


class ChoiceForm(Form):
    role = ChoiceField(
        "Role",
        choices=[("Admin", "admin"), ("User", "user"), ("Guest", "guest")],
    )


class TextForm(Form):
    notes = TextField("Notes")


class CrossFieldForm(Form):
    password = StringField("Password", required=True)
    confirm = StringField("Confirm", required=True)

    def clean_form(self):
        if self.password.value != self.confirm.value:
            self.add_error("confirm", "Passwords do not match")
        return True  # add_error sets the flag; clean() returns False automatically


# ── Test apps ───────────────────────────────────────────────────


class SimpleFormApp(App):
    submitted_data: dict | None = None
    cancelled: bool = False

    def compose(self) -> ComposeResult:
        self.form = SimpleForm()
        yield self.form.layout()

    def on_base_form_submitted(self, event: BaseForm.Submitted) -> None:
        self.submitted_data = event.form.get_data()

    def on_base_form_cancelled(self, event: BaseForm.Cancelled) -> None:
        self.cancelled = True


class PrefilledApp(App):
    def compose(self) -> ComposeResult:
        self.form = SimpleForm(data={"name": "Alice", "age": "30"})
        yield self.form.layout()


class ChoiceApp(App):
    def compose(self) -> ComposeResult:
        self.form = ChoiceForm()
        yield self.form.layout()


class TextApp(App):
    def compose(self) -> ComposeResult:
        self.form = TextForm()
        yield self.form.layout()


class HelpTextApp(App):
    def compose(self) -> ComposeResult:
        self.form = HelpTextForm()
        yield self.form.layout()


class CrossFieldApp(App):
    submitted_data: dict | None = None

    def compose(self) -> ComposeResult:
        self.form = CrossFieldForm()
        yield self.form.layout()

    def on_base_form_submitted(self, event: BaseForm.Submitted) -> None:
        self.submitted_data = event.form.get_data()


# ── Mounting tests ──────────────────────────────────────────────


class TestFormMounting:
    async def test_layout_present(self):
        async with SimpleFormApp().run_test() as pilot:
            layout = pilot.app.query_one(DefaultFormLayout)
            assert layout is not None
            assert layout.form is pilot.app.form

    async def test_title_shown(self):
        async with SimpleFormApp().run_test() as pilot:
            title_label = pilot.app.query_one(".form-title", Label)
            assert "Simple Form" in title_label.render().plain

    async def test_submit_button(self):
        async with SimpleFormApp().run_test() as pilot:
            assert pilot.app.query_one("#submit", Button) is not None

    async def test_cancel_button(self):
        async with SimpleFormApp().run_test() as pilot:
            assert pilot.app.query_one("#cancel", Button) is not None

    async def test_field_widgets_rendered(self):
        async with SimpleFormApp().run_test() as pilot:
            fws = list(pilot.app.query(FieldWidget))
            assert len(fws) == 2

    async def test_prefilled_values(self):
        async with PrefilledApp().run_test() as pilot:
            assert pilot.app.form.name.value == "Alice"
            assert pilot.app.form.age.value == 30


# ── Submission tests ────────────────────────────────────────────


class TestFormSubmission:
    async def test_submit_valid(self):
        async with SimpleFormApp().run_test() as pilot:
            pilot.app.form.set_data({"name": "Bob"})
            await pilot.click("#submit")
            await pilot.pause()
            assert pilot.app.submitted_data is not None
            assert pilot.app.submitted_data["name"] == "Bob"

    async def test_submit_invalid_blocked(self):
        async with SimpleFormApp().run_test() as pilot:
            await pilot.click("#submit")
            await pilot.pause()
            assert pilot.app.submitted_data is None
            assert pilot.app.form.name.has_error is True

    async def test_cancel(self):
        async with SimpleFormApp().run_test() as pilot:
            await pilot.click("#cancel")
            await pilot.pause()
            assert pilot.app.cancelled is True


# ── Keyboard shortcuts ──────────────────────────────────────────


class TestKeyboardShortcuts:
    async def test_escape_cancels(self):
        async with SimpleFormApp().run_test() as pilot:
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.cancelled is True


# ── Input interaction ───────────────────────────────────────────


class TestInputInteraction:
    async def test_type_into_field(self):
        async with SimpleFormApp().run_test() as pilot:
            inputs = list(pilot.app.query(Input))
            if inputs:
                inputs[0].focus()
                await pilot.press(*"Alice")
                await pilot.pause()
                assert pilot.app.form.name.value == "Alice"


# ── Help text ───────────────────────────────────────────────────


class TestHelpText:
    async def test_help_below_rendered(self):
        async with HelpTextApp().run_test() as pilot:
            from textual.widgets import Static

            help_statics = list(pilot.app.query(".field-help"))
            assert any(
                "email" in s.render().plain.lower()
                for s in help_statics
            )

# ── Widget types ────────────────────────────────────────────────


class TestWidgetTypes:
    async def test_select_mounted(self):
        app = ChoiceApp()
        async with app.run_test() as pilot:
            selects = list(pilot.app.query(Select))
            assert len(selects) >= 1

    async def test_textarea_mounted(self):
        async with TextApp().run_test() as pilot:
            areas = list(pilot.app.query(TextArea))
            assert len(areas) >= 1


# ── set_data while mounted ──────────────────────────────────────


class TestSetDataMounted:
    async def test_set_data(self):
        async with SimpleFormApp().run_test() as pilot:
            pilot.app.form.set_data({"name": "Charlie", "age": "40"})
            await pilot.pause()
            assert pilot.app.form.name.value == "Charlie"
            assert pilot.app.form.age.value == 40


# ── Validation error display ───────────────────────────────────


class TestValidationDisplay:
    async def test_error_shown_after_submit(self):
        async with SimpleFormApp().run_test() as pilot:
            await pilot.click("#submit")
            await pilot.pause()
            assert pilot.app.form.name.has_error is True
            error_labels = list(pilot.app.query(".field-error.has-error"))
            assert len(error_labels) > 0


# ── Cross-field validation via clean ────────────────────────────


class TestCleanIntegration:
    async def test_cross_field_blocks_submit(self):
        async with CrossFieldApp().run_test() as pilot:
            pilot.app.form.set_data({"password": "abc", "confirm": "xyz"})
            await pilot.click("#submit")
            await pilot.pause()
            assert pilot.app.submitted_data is None

    async def test_cross_field_allows_submit(self):
        async with CrossFieldApp().run_test() as pilot:
            pilot.app.form.set_data({"password": "abc", "confirm": "abc"})
            await pilot.click("#submit")
            await pilot.pause()
            assert pilot.app.submitted_data is not None
            assert pilot.app.submitted_data["password"] == "abc"
