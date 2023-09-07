import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from core import models
from core.tests import test_factory

@pytest.fixture
def user() -> models.User:
    user = test_factory.UserFactory()
    user.save()
    return user

@pytest.fixture
def admin_user() -> models.User:
    admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123',
        )
    admin_user.save()
    return admin_user

@pytest.fixture
def api_client():
    print("api client created")
    return APIClient()

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user)
    return api_client

@pytest.fixture
def admin_auth_client(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    return api_client

@pytest.fixture
def recipe() -> models.Recipe:
    recipe = test_factory.RecipeFactory()
    return recipe