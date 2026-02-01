"""Tests that simulate actual user input through rendered forms"""
import pytest
from textual.app import App
from textual_wtf import Form, StringField, IntegerField, BooleanField


class SimpleForm(Form):
    """Simple form for testing"""
    name = StringField(label="Name", required=True)
    age = IntegerField(label="Age", min_value=0, max_value=130)
    active = BooleanField(label="Active")


@pytest.mark.asyncio
class TestUserInput:
    """Simulate user interactions and verify data flows correctly"""

    async def test_type_into_string_field(self):
        """Typing into a StringField updates form data"""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = SimpleForm()

            def compose(self):
                yield self.form.render()

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.click(app.form.name.widget)
            await pilot.press("A", "l", "i", "c", "e")
            await pilot.pause()

            assert app.form.get_data()["name"] == "Alice"

    async def test_toggle_checkbox(self):
        """Clicking a BooleanField checkbox toggles its value"""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = SimpleForm()

            def compose(self):
                yield self.form.render()

        app = TestApp()
        async with app.run_test() as pilot:
            widget = app.form.active.widget

            assert app.form.get_data()["active"] is False

            await pilot.click(widget)
            await pilot.pause()
            assert app.form.get_data()["active"] is True

            await pilot.click(widget)
            await pilot.pause()
            assert app.form.get_data()["active"] is False

    async def test_edit_prepopulated_field(self):
        """Editing a pre-populated field updates form data correctly"""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = SimpleForm(data={
                    "name": "Alice",
                    "age": 30,
                    "active": True,
                })

            def compose(self):
                yield self.form.render()

        app = TestApp()
        async with app.run_test() as pilot:
            # Verify pre-populated data is present
            assert app.form.get_data()["name"] == "Alice"

            # Select all and replace
            await pilot.click(app.form.name.widget)
            await pilot.press("home", "shift+end")
            await pilot.press("B", "o", "b")
            await pilot.pause()

            assert app.form.get_data()["name"] == "Bob"

    async def test_submit_posts_message_with_data(self):
        """Submitting a valid form posts Form.Submitted with correct data"""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = SimpleForm()
                self.submitted_data = None

            def compose(self):
                yield self.form.render()

            def on_form_submitted(self, event: Form.Submitted):
                self.submitted_data = event.form.get_data()

        app = TestApp()
        async with app.run_test() as pilot:
            # Fill in the required field
            await pilot.click(app.form.name.widget)
            await pilot.press("A", "l", "i", "c", "e")
            await pilot.pause()

            # Submit
            await pilot.click(app.query_one("#submit"))
            await pilot.pause()

            assert app.submitted_data is not None
            assert app.submitted_data["name"] == "Alice"

    async def test_submit_blocked_by_required_field(self):
        """Submitting with a missing required field does not post Form.Submitted"""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = SimpleForm()  # name is required
                self.submitted = False

            def compose(self):
                yield self.form.render()

            def on_form_submitted(self, event: Form.Submitted):
                self.submitted = True

        app = TestApp()
        async with app.run_test() as pilot:
            # Leave 'name' empty — it's required
            # Click submit
            await pilot.click(app.query_one("#submit"))
            await pilot.pause()

            assert app.submitted is False
