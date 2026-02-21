"""Integration tests using Textual's run_test() headless runner."""
from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from textual_wtf import (
    BooleanField,
    DefaultFormLayout,
    Form,
    FormLayout,
    IntegerField,
    StringField,
    TextField,
)
from textual_wtf.layouts import FieldContainer


# ── Test app helper ───────────────────────────────────────────────────────────

def make_app(form: Form) -> App:
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


# ── Rendering ─────────────────────────────────────────────────────────────────

class TestRendering:
    async def test_default_layout_mounts(self):
        class MyForm(Form):
            name = StringField(label="Name")

        app = make_app(MyForm())
        async with app.run_test():
            assert app.query_one(DefaultFormLayout) is not None

    async def test_field_containers_rendered(self):
        class MyForm(Form):
            name  = StringField(label="Name")
            email = StringField(label="Email")

        app = make_app(MyForm())
        async with app.run_test():
            assert len(app.query(FieldContainer)) == 2

    async def test_inner_widgets_rendered(self):
        class MyForm(Form):
            name  = StringField(label="Name")
            email = StringField(label="Email")

        app = make_app(MyForm())
        async with app.run_test():
            from textual_wtf.widgets import FormInput
            assert len(app.query(FormInput)) == 2

    async def test_submit_and_cancel_buttons_present(self):
        class MyForm(Form):
            name = StringField(label="Name")

        app = make_app(MyForm())
        async with app.run_test():
            assert app.query_one("#submit", Button) is not None
            assert app.query_one("#cancel", Button) is not None

    async def test_duplicate_render_raises(self):
        class MyForm(Form):
            name = StringField(label="Name")

        class DuplicateLayout(FormLayout):
            def compose_form(self):
                yield self.form.name()
                yield self.form.name()  # second yield → FormError

        class MyForm2(Form):
            layout_class = DuplicateLayout
            name = StringField(label="Name")

        app = make_app(MyForm2())
        with pytest.raises(Exception):
            async with app.run_test():
                pass

    async def test_bound_field_not_in_widget_tree(self):
        """BoundField is a plain object; it must not appear in the DOM."""
        from textual_wtf import BoundField
        from textual.widget import Widget

        class MyForm(Form):
            name = StringField(label="Name")

        app = make_app(MyForm())
        async with app.run_test():
            # BoundField is not a Widget, so querying it would raise a TypeError.
            # We verify the absence by checking it's not a Widget subclass.
            assert not issubclass(BoundField, Widget)


# ── User input ────────────────────────────────────────────────────────────────

class TestUserInput:
    async def test_typing_updates_bound_field_value(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            inp = app.query_one(FormInput)
            await pilot.click(inp)
            await pilot.press("A", "l", "i", "c", "e")
            assert form.name.value == "Alice"

    async def test_integer_field_value_converted(self):
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
            before = form.active.value
            await pilot.click(cb)
            assert form.active.value != before

    async def test_programmatic_set_reflected_in_widget(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            form.name.value = "Prefilled"
            await pilot.pause()
            assert app.query_one(FormInput).value == "Prefilled"

    async def test_is_dirty_set_on_user_input(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            assert not form.name.is_dirty
            await pilot.click(app.query_one(FormInput))
            await pilot.press("X")
            assert form.name.is_dirty


# ── Validation ────────────────────────────────────────────────────────────────

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
            await pilot.click(app.query_one(FormInput))
            await pilot.press("B", "o", "b")
            await pilot.click("#submit")
            assert app.submitted_data is not None
            assert app.submitted_data["name"] == "Bob"

    async def test_cancel_posts_message(self):
        class MyForm(Form):
            name = StringField(label="Name")

        app = make_app(MyForm())
        async with app.run_test() as pilot:
            await pilot.click("#cancel")
            assert app.cancelled

    async def test_blur_triggers_validation(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            from textual_wtf.widgets import FormInput
            await pilot.click(app.query_one(FormInput))
            await pilot.press("tab")   # move focus away → blur
            assert form.name.has_error

    async def test_error_widget_shown_after_validation(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            await pilot.click("#submit")
            error = app.query_one(".field-error", Static)
            assert error.display

    async def test_error_cleared_after_fix(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        app = make_app(form)
        async with app.run_test() as pilot:
            await pilot.click("#submit")
            assert form.name.has_error

            from textual_wtf.widgets import FormInput
            await pilot.click(app.query_one(FormInput))
            await pilot.press("A", "l", "i", "c", "e")
            await pilot.click("#submit")
            assert not form.name.has_error

    def test_render_resets_rendered_flag(self):
        """FormLayout.compose() resets _rendered so re-renders work."""
        from textual_wtf import DefaultFormLayout

        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        # Simulate what compose() does.
        form.name()
        assert form.name._rendered

        layout = DefaultFormLayout(form)
        # compose() resets state before calling compose_form().
        list(layout.compose())
        assert not form.name._rendered  # reset then re-called internally

    async def test_render_resets_rendered_flag(self):
        """FormLayout.compose() resets _rendered so re-renders work."""
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()

        # Manually call once to set the flag, simulating a prior render.
        form.name()
        assert form.name._rendered

        # Now mount in a real app — compose() resets state before compose_form().
        app = make_app(form)
        async with app.run_test():
            assert not form.name._rendered  # reset then re-called by compose_form()

# ── Custom layouts ────────────────────────────────────────────────────────────

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
        async with app.run_test():
            assert len(app.query(FieldContainer)) == 2

    async def test_beside_label_style_creates_field_row(self):
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
        async with app.run_test():
            assert len(app.query(".field-row")) == 1

    async def test_initial_value_shown_in_widget(self):
        class MyForm(Form):
            name = StringField(label="Name", initial="Hello")

        app = make_app(MyForm())
        async with app.run_test():
            from textual_wtf.widgets import FormInput
            assert app.query_one(FormInput).value == "Hello"

    async def test_disabled_field_not_editable(self):
        class MyForm(Form):
            name = StringField(label="Name", disabled=True)

        app = make_app(MyForm())
        async with app.run_test():
            from textual_wtf.widgets import FormInput
            assert app.query_one(FormInput).disabled

    async def test_call_site_disabled_override(self):
        class MyForm(Form):
            name = StringField(label="Name")

        class DisableLayout(FormLayout):
            def compose_form(self):
                yield self.form.name(disabled=True)
                with Horizontal(id="buttons"):
                    yield Button("Submit", id="submit", variant="primary")
                    yield Button("Cancel", id="cancel")

        app = make_app(MyForm(layout_class=DisableLayout))
        async with app.run_test():
            from textual_wtf.widgets import FormInput
            assert app.query_one(FormInput).disabled


# ── Composed form integration ─────────────────────────────────────────────────

class TestComposedFormIntegration:
    async def test_all_fields_rendered(self):
        class AddressForm(Form):
            street = StringField(label="Street")
            city   = StringField(label="City")

        class OrderForm(Form):
            billing  = AddressForm.compose(prefix="billing")
            shipping = AddressForm.compose(prefix="shipping")

        app = make_app(OrderForm())
        async with app.run_test():
            assert len(app.query(FieldContainer)) == 4

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
