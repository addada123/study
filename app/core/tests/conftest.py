import pytest

from rest_framework.test import APIClient

from core import models
from core.tests import test_factory

@pytest.fixture
def api_client():
    print("api client created")
    return APIClient()

@pytest.fixture
def user() -> test_factory.UserFactory:
    user = test_factory.UserFactory()
    user.save()
    return user

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user)
    return api_client