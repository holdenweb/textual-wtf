from textual_forms.demo import build_app
from textual_forms import StringField

from . import one_field_app

import pytest

#s@pytest.mark.skip
@pytest.mark.asyncio(loop_scope="function")
async def test_typed_input():
    field = StringField(id="sf", required=True)
    app = one_field_app(field)()
    async with app.run_test() as pilot:
        test_field = app.query_one("#sf")
        test_field.focus()
        for c in "Steve Holden":
            await pilot.press(c)
        assert test_field.value == "Steve Holden"

@pytest.mark.asyncio(loop_scope="function")
async def test_empty_ok():
    field = StringField(id="sf", required=False)
    app = one_field_app(field)()
    async with app.run_test() as pilot:
        test_field = app.query_one("#sf")
        test_field.focus()
        assert test_field.value == ""
        assert app.form.validate()

@pytest.mark.asyncio(loop_scope="function")
async def test_empty_none():
    field = StringField(id="sf", required=False, value="something")
    app = one_field_app(field)()
    async with app.run_test() as pilot:
        field.value = None
        assert field.widget.value == ""
        assert field.value is None

@pytest.mark.skip  # Skip until https://github.com/Textualize/textual/issues/5917 fixed
@pytest.mark.asyncio(loop_scope="function")
async def test_not_empty_ok():
    field = StringField(id="sf", required=True)
    app = one_field_app(field)()
    async with app.run_test() as pilot:
        test_field = app.query_one("#sf")
        test_field.focus()
        assert test_field.value == ""
        assert not app.form.validate()


