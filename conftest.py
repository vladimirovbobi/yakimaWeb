"""Pytest fixtures shared across all apps."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="member@example.com",
        password="pa$$word-12345",
    )


@pytest.fixture
def realtor(db):
    return User.objects.create_user(
        email="realtor@example.com",
        password="pa$$word-12345",
        is_realtor=True,
    )


@pytest.fixture
def staff(db):
    return User.objects.create_user(
        email="staff@example.com",
        password="pa$$word-12345",
        is_staff=True,
    )
