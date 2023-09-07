from unittest.mock import patch
from django.urls import reverse
from core.tests import test_factory

from django.contrib.auth import get_user_model
from decimal import Decimal

from core import models
import pytest
pytestmark = pytest.mark.django_db


def create_user(email = 'user@example.com', password = 'testpass123'):
    return get_user_model().objects.create_user(email, password)

class TestsModel:
    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = test_factory.UserFactory.create(email=email, password=password)
        assert user.email == email
        assert user.check_password(password)

    def test_new_user_email_normalized(self):
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            assert user.email == expected

    def test_new_user_without_email_raises_error(self):
        try:
            user=get_user_model().objects.create_user('', 'test123')
        except Exception as E:
            assert type(E) is ValueError

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )
        assert user.is_superuser is True
        assert user.is_staff is True
        

    def test_create_recipe(self):
        user = test_factory.UserFactory.create()
        recipe = test_factory.RecipeFactory.create(user=user)
        assert str(recipe) == recipe.title

    def test_create_tag(self):
        user = test_factory.UserFactory.create()

        tag = test_factory.TagsFactory.create(user=user)
        assert str(tag) == tag.name

    def test_create_ingredient(self):
        user = test_factory.UserFactory.create()
        ingredient = test_factory.IngredientsFactory.create(user=user)
        assert str(ingredient) == ingredient.name

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')
        assert file_path == f'uploads/recipe/{uuid}.jpg'
