"""Pytest configuration"""
import pytest


@pytest.fixture
def sample_form_data():
    """Sample form data for testing"""
    return {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
    }


@pytest.fixture
def sample_choices():
    """Sample choices for select fields"""
    return [
        ("us", "United States"),
        ("uk", "United Kingdom"),
        ("ca", "Canada"),
    ]
