"""Integration tests using Textual's run_test() headless runner.

These tests verify rendering, user interaction, validation feedback, and
form submission through the full Textual widget stack.
"""
from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button

from textual_wtf import (
    BooleanField,
    ChoiceField,
    DefaultFormLayout,
    Form,
    FormLayout,
    IntegerField,
    Required,
    StringField,
    TextField,
    ValidationError,
)


# ── Test helpers ──────────────────────────────────────────────────────────────

def make_app(form: Form) -> App:
    """Wrap a form in a minimal Textual App for testing."""

    class TestApp(App):
        CSS = "Screen { align: center middle; }"

        def __init__(self, form: Form) -> None:
            super().__init__()
            self.form = form
            self.submitted_data: dict | None = None
            self.cancelled = False

        def compose(self) -> ComposeResult:
            yield self.form.render()

        def on_form_layout_submitted(self, event: FormLayout.Submitted) -> None:
            self.submitted_data = event.form.get_data()

        def on_form_layout_cancelled(self, event: FormLayout.Cancelled) -> None:
            self.cancelled = True

    return TestApp(form)


# ── Rendering tests ───────────────────────────────────────────────────────────

class TestRendering:
    async def test_default_layout_mounts(self):
        class SimpleForm(Form):
            name = StringField(label="Name")

        app = make_app(SimpleForm())
        async with app.run_test() as pilot:
            layout = app.query_one(DefaultFormLayout)
            assert layout is not None

    async def test_all_fields_rendered(self):
        class MyForm(Form):
            name  = StringField(label="Name")
            email = StringField(label="Email")

        app = make_app(MyForm())
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inputs = app.query(FormInput)
            assert len(inputs) == 2

    async def test_submit_and_cancel_buttons_present(self):
        class MyForm(Form):
            name = StringField(label="Name")

        app = make_app(MyForm())
        async with app.run_test() as pilot:
            submit = app.query_one("#submit", Button)
            cancel = app.query_one("#cancel", Button)
            assert submit is not None
            assert cancel is not None

    async def test_duplicate_field_render_raises(self):
        class MyForm(Form):
            name = StringField(label="Name")

        class DuplicateLayout(FormLayout):
            def compose_form(self):
                yield self.form.name()
                yield self.form.name()  # duplicate!

        class MyFormWithBadLayout(Form):
            layout_class = DuplicateLayout
            name = StringField(label="Name")

        app = make_app(MyFormWithBadLayout())
        with pytest.raises(Exception):  # FormError raised during compose
            async with app.run_test():
                pass


# ── User input tests ──────────────────────────────────────────────────────────

class TestUserInput:
    async def test_typing_updates_value(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            await pilot.click(inp)
            await pilot.press("A", "l", "i", "c", "e")
            # Value is read from the widget via reactive
            assert form.name.value == "Alice"

    async def test_integer_field_accepts_numbers(self):
        class MyForm(Form):
            age = IntegerField(label="Age")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            await pilot.click(inp)
            await pilot.press("4", "2")
            assert form.age.value == 42

    async def test_boolean_field_toggles(self):
        class MyForm(Form):
            active = BooleanField(label="Active")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormCheckbox
            cb = app.query_one(FormCheckbox)
            initial = form.active.value
            await pilot.click(cb)
            assert form.active.value != initial

    async def test_programmatic_value_shown_in_widget(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            form.name.value = "Prefilled"
            await pilot.pause()  # allow reactive to propagate
            inp = app.query_one(FormInput)
            assert inp.value == "Prefilled"


# ── Validation tests ──────────────────────────────────────────────────────────

class TestValidation:
    async def test_required_field_blocks_submit(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            await pilot.click("#submit")
            assert app.submitted_data is None
            assert form.name.has_error

    async def test_valid_form_submits(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            await pilot.click(inp)
            await pilot.press("B", "o", "b")
            await pilot.click("#submit")
            assert app.submitted_data is not None
            assert app.submitted_data["name"] == "Bob"

    async def test_cancel_posts_cancelled_message(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            await pilot.click("#cancel")
            assert app.cancelled

    async def test_error_cleared_after_correction(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            # Submit empty → error.
            await pilot.click("#submit")
            assert form.name.has_error

            # Type something → re-submit → no error.
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            await pilot.click(inp)
            await pilot.press("A", "l", "i", "c", "e")
            await pilot.click("#submit")
            assert not form.name.has_error


# ── Custom layout tests ───────────────────────────────────────────────────────

class TestCustomLayout:
    async def test_custom_compose_form(self):
        class MyForm(Form):
            first = StringField(label="First")
            last  = StringField(label="Last")

        class SideBySide(FormLayout):
            def compose_form(self):
                with Horizontal():
                    yield self.form.first(label_style="above")
                    yield self.form.last(label_style="above")
                with Horizontal(id="buttons"):
                    yield Button("Submit", id="submit", variant="primary")
                    yield Button("Cancel", id="cancel")

        form = MyForm(layout_class=SideBySide)
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inputs = list(app.query(FormInput))
            assert len(inputs) == 2

    async def test_call_site_label_style_override(self):
        """label_style passed to __call__ takes effect in composed DOM."""

        class MyForm(Form):
            name = StringField(label="Name")

        class BesideLayout(FormLayout):
            def compose_form(self):
                yield self.form.name(label_style="beside")
                with Horizontal(id="buttons"):
                    yield Button("Submit", id="submit", variant="primary")
                    yield Button("Cancel", id="cancel")

        form = MyForm(layout_class=BesideLayout)
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual.containers import Horizontal as H
            # "beside" style wraps label+input in a Horizontal.
            rows = app.query(".field-row")
            assert len(rows) == 1

    async def test_initial_value_displayed(self):
        class MyForm(Form):
            name = StringField(label="Name", initial="Hello")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            assert inp.value == "Hello"

    async def test_disabled_field_not_editable(self):
        class MyForm(Form):
            name = StringField(label="Name", disabled=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            assert inp.disabled


# ── Composed form integration ─────────────────────────────────────────────────

class TestComposedFormIntegration:
    async def test_composed_form_renders_all_fields(self):
        class AddressForm(Form):
            street = StringField(label="Street")
            city   = StringField(label="City")

        class OrderForm(Form):
            billing  = AddressForm.compose(prefix="billing")
            shipping = AddressForm.compose(prefix="shipping")

        form = OrderForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inputs = list(app.query(FormInput))
            assert len(inputs) == 4  # 2 billing + 2 shipping

    async def test_composed_field_value_in_submitted_data(self):
        class AddressForm(Form):
            street = StringField(label="Street")

        class OrderForm(Form):
            billing = AddressForm.compose(prefix="billing")

        form = OrderForm()
        form.billing_street.value = "10 Downing St"
        app = make_app(form)
        async with app.run_test() as pilot:
            await pilot.click("#submit")
            assert app.submitted_data is not None
            assert app.submitted_data["billing_street"] == "10 Downing St"
