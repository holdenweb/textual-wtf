"""Shared test fixtures and helpers."""
from __future__ import annotations

import pytest
from textual_wtf import (
    BooleanField,
    ChoiceField,
    Form,
    IntegerField,
    StringField,
    TextField,
)


# ── Simple re-usable form classes ─────────────────────────────────────────────

class ContactForm(Form):
    name  = StringField(label="Name",  required=True)
    email = StringField(label="Email", help_text="Your email address")
    age   = IntegerField(label="Age",  min_value=0, max_value=150)


class ChoiceForm(Form):
    colour = ChoiceField(
        label="Colour",
        choices=[("Red", "red"), ("Green", "green"), ("Blue", "blue")],
        required=True,
    )


class BoolForm(Form):
    active = BooleanField(label="Active", initial=True)


class MultilineForm(Form):
    notes = TextField(label="Notes")


@pytest.fixture
def contact_form() -> ContactForm:
    return ContactForm()


@pytest.fixture
def contact_form_with_data() -> ContactForm:
    return ContactForm(data={"name": "Alice", "email": "alice@example.com", "age": "30"})
