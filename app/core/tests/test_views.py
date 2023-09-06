from core.tests import test_factory

import pytest

from django.urls import reverse

from decimal import Decimal
import json

from core import models

pytestmark = pytest.mark.django_db

INGREDIENTS_URL = reverse('recipe:ingredient-list')
TAGS_URL = reverse('recipe:tag-list')
RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(model_name, item_id):
    return reverse(f"recipe:{model_name}-detail", args=[item_id])

class TestIngredientsViewsWOAuth:

    def test_private_get(self, api_client):
        ingredients = api_client.get(INGREDIENTS_URL)
        recipes = api_client.get(RECIPES_URL) #Everyone can see recipes
        tags = api_client.get(TAGS_URL)
        assert [ingredients.status_code, recipes.status_code, tags.status_code] == [401, 200, 401] 

class TestIngredientsViewsWAuth:

    def test_login_permission(self, auth_client, user):
        ingredients = auth_client.get(INGREDIENTS_URL)
        tags = auth_client.get(TAGS_URL)
        assert [ingredients.status_code, tags.status_code] == [200, 200]


    """def test_create_endpoints(self, api_client, user):
        api_client.force_authenticate(user)
        ingredient_data = test_factory.IngredientsFactory(user=user)
        tag_data = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory()
        serialized_recipe = RecipeSerializer(recipe_data)
        print(serialized_recipe)
        ingredients = api_client.post(RECIPES_URL, json.dumps(serialized_recipe), content_type='application/json')
        assert ingredients.status_code == 201"""
    
    def test_create_recipe(self, auth_client, user):
        tag = test_factory.TagsFactory(user = user)
        ingredient = test_factory.IngredientsFactory(user = user)
        payload = {
            "title": "Sample recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
            "tags": [tag.id],
            "ingredients": [ingredient.id]
        }
        #payload = test_factory.RecipeFactory.build(user = user, tags = [tag.id], ingredients = [ingredient.id])
        res_recipe = auth_client.post(RECIPES_URL, payload)
        assert res_recipe.status_code == 201
        
    def test_endpoints_delete_recipe(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory(user=user)
        tags = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=(ingredients, tags))
        recipe_url = detail_url("recipe", recipe_data.id)
        assert models.Recipe.objects.count() == 1
        response = auth_client.delete(recipe_url)
        assert [models.Recipe.objects.count(), response.status_code] == [0, 204]

    def test_endpoints_patch_recipe(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory(user=user)
        tags = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=(ingredients, tags))
        starting_title = recipe_data.title
        payload = {"title": "TEST!"}
        url = detail_url("recipe", recipe_data.id)
        auth_client.patch(url, payload)
        recipe_data.refresh_from_db()
        assert recipe_data.title != starting_title
        assert recipe_data.title == payload["title"]

    def test_endpoints_update_recipe(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory(user=user)
        tags = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=(ingredients, tags))
        recipe_data_payload = test_factory.RecipeFactory.build(user=user)
        assert recipe_data != recipe_data_payload
        payload = {"title": recipe_data_payload.title,
                   "time_minutes": recipe_data_payload.time_minutes,
                   "price": recipe_data_payload.price}
        url = detail_url("recipe", recipe_data.id)
        auth_client.put(url, payload)
        recipe_data.refresh_from_db()
        assert recipe_data.title == payload["title"]
        assert recipe_data.time_minutes == payload["time_minutes"]
        assert recipe_data.price == payload["price"]