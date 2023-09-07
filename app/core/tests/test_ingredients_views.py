import pytest

from django.urls import reverse
from core.tests import test_factory
from core import models
from recipe import serializers

pytestmark = pytest.mark.django_db

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(model_name, item_id):
    return reverse(f"recipe:{model_name}-detail", args=[item_id])

class TestTagsWOAuth:

    def test_retrieve_ingredients(self, api_client):
        test_factory.TagsFactory.create_batch(2)
        res = api_client.get(INGREDIENTS_URL)
        assert res.status_code == 401

class TestsTagsWAuth:
    def test_retrieve_ingredients(self, auth_client, user):
        test_factory.IngredientsFactory.create_batch(2, user=user)

        res = auth_client.get(INGREDIENTS_URL)

        ingredients = models.Ingredient.objects.all().order_by('-name')
        serializer = serializers.IngredientSerializer(ingredients, many=True)
        assert res.status_code == 200
        assert res.data == serializer.data

    def test_ingredients_limited_to_user(self, auth_client, user):
        user2 = test_factory.UserFactory()
        test_factory.IngredientsFactory.create(user=user2)
        ingredient = test_factory.IngredientsFactory.create(user=user)
        res = auth_client.get(INGREDIENTS_URL)
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['name'] == ingredient.name
        assert res.data[0]['id'] == ingredient.id
        
    def test_update_ingredient(self, auth_client, user):
        ingredient = test_factory.IngredientsFactory.create(user=user)
        payload = {'name': 'Coriander'}
        url = detail_url("ingredient", ingredient.id)
        res = auth_client.patch(url, payload)
        assert res.status_code == 200
        ingredient.refresh_from_db()
        assert ingredient.name == payload["name"]


    def test_delete_ingredient(self, auth_client, user):
        ingredient = test_factory.IngredientsFactory.create(user=user)
        url = detail_url("ingredient", ingredient.id)
        res = auth_client.delete(url)
        assert res.status_code == 204
        assert models.Ingredient.objects.filter(id=ingredient.id).exists() == False
        
    
    def test_filter_ingredients_assigned_to_recipes(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory.create_batch(2, user=user)
        test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes = [ingredients[0]])

        res = auth_client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = serializers.IngredientSerializer(ingredients[0])
        s2 = serializers.IngredientSerializer(ingredients[1])
        assert s1.data in res.data
        assert s2.data not in res.data
        
    def test_filtered_ingredients_unique(self, auth_client, user):
        ing = test_factory.IngredientsFactory.create(user=user)
        test_factory.IngredientsFactory.create(user=user, name='Lentils')
        test_factory.RecipeFactory.create_batch(2, user=user, ingredients_and_tags_and_likes = [ing])
        

        res = auth_client.get(INGREDIENTS_URL, {'assigned_only': 1})
        assert len(res.data) == 1
