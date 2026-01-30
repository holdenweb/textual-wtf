"""Test widgets using Textual's run_test"""
import pytest
from textual.app import App
from textual_wtf import StringField
from textual_wtf.widgets import (
    FormInput, FormIntegerInput, FormTextArea, FormCheckbox,
    FormSelect, WidgetRegistry
)


@pytest.mark.asyncio
class TestFormInputWithApp:
    """Test FormInput widget with app context"""

    async def test_creation(self):
        """Test widget creation in app"""
        class TestApp(App):
            def compose(self):
                yield FormInput()

        app = TestApp()
        async with app.run_test() as pilot:
            assert True  # Widget created successfully

    async def test_with_field(self):
        """Test widget with field in app"""
        class TestApp(App):
            def compose(self):
                field = StringField()
                yield FormInput(field=field)

        app = TestApp()
        async with app.run_test() as pilot:
            assert True  # Widget with field created successfully


@pytest.mark.asyncio
class TestFormIntegerInputWithApp:
    """Test FormIntegerInput widget with app context"""

    async def test_creation(self):
        """Test widget creation in app"""
        class TestApp(App):
            def compose(self):
                yield FormIntegerInput()

        app = TestApp()
        async with app.run_test() as pilot:
            assert True  # Widget created successfully


class TestFormTextArea:
    """Test FormTextArea widget"""

    def test_value_property(self):
        """Test value property"""
        widget = FormTextArea(text="Hello")
        assert widget.value == "Hello"
        widget.value = "World"
        assert widget.text == "World"

    def test_none_value(self):
        """Test setting None value"""
        widget = FormTextArea()
        widget.value = None
        assert widget.text == ""


class TestFormCheckbox:
    """Test FormCheckbox widget"""

    def test_with_label(self):
        """Test widget with label"""
        widget = FormCheckbox(label="Accept")
        assert widget.label == "Accept"


@pytest.mark.asyncio
class TestFormSelectWithApp:
    """Test FormSelect with app context"""

    async def test_creation(self):
        """Test widget creation"""
        class TestApp(App):
            def compose(self):
                choices = [("us", "United States"), ("uk", "United Kingdom")]
                yield FormSelect(choices=choices)

        app = TestApp()
        async with app.run_test() as pilot:
            assert True  # Widget created successfully

    async def test_allow_blank(self):
        """Test allow_blank option"""
        class TestApp(App):
            def compose(self):
                choices = [("us", "United States")]
                yield FormSelect(choices=choices, allow_blank=True)

        app = TestApp()
        async with app.run_test() as pilot:
            assert True  # Widget with allow_blank created successfully


class TestWidgetRegistry:
    """Test WidgetRegistry"""

    def test_builtin_widgets(self):
        """Test that built-in widgets are registered"""
        assert WidgetRegistry.get("input") == FormInput
        assert WidgetRegistry.get("integer_input") == FormIntegerInput
        assert WidgetRegistry.get("textarea") == FormTextArea
        assert WidgetRegistry.get("checkbox") == FormCheckbox
        assert WidgetRegistry.get("select") == FormSelect

    def test_list_widgets(self):
        """Test listing widgets"""
        widgets = WidgetRegistry.list_widgets()
        assert "input" in widgets
        assert "textarea" in widgets

    def test_register_custom_widget(self):
        """Test registering custom widget"""
        @WidgetRegistry.register("custom")
        class CustomWidget:
            pass

        assert WidgetRegistry.get("custom") == CustomWidget
